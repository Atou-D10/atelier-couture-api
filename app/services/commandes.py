from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.commande import Commande
from app.models.client import Client
from app.models.historique_statut import HistoriqueStatut
from app.models.ligne_commande import LigneCommande
from app.models.mesure import Mesure
from app.models.utilisateur import Utilisateur
from app.models.enums import RoleUtilisateur, StatutCommande

from app.schemas.commande import CommandeCreate,  CommandeUpdate, LigneCommandeCreate

from app.exceptions import ConflitError,InterditError, IntrouvableError, ValidationMetierError
from app.models.type_vetement import TypeVetement

def est_en_retard(commande: Commande, aujourdhui: date | None = None) -> bool:
    """RG11 : date prévue dépassée et commande ni livrée ni annulée."""
    aujourdhui = aujourdhui or date.today()
    return commande.date_livraison_prevue < aujourdhui and commande.statut not in (
        StatutCommande.livree,
        StatutCommande.annulee,
    )


def vers_liste(commande: Commande) -> dict:
    """Construit un élément de CommandeListe (route 25 et 12)."""
    return {
        "id": commande.id,
        "numero": commande.numero,
        "client_id": commande.client_id,
        "client_nom": f"{commande.client.prenom} {commande.client.nom}",
        "statut": commande.statut,
        "date_commande": commande.date_commande,
        "date_livraison_prevue": commande.date_livraison_prevue,
        "montant_total": commande.montant_total,
        "montant_paye": commande.montant_paye,
        "solde": commande.solde,
        "en_retard": est_en_retard(commande),
    }

# ---------- RG5 : numéro de commande ----------

def formater_numero(annee: int, commande_id: int) -> str:
    """CMD-AAAA-NNNNN, ex. CMD-2026-00017."""
    return f"CMD-{annee}-{commande_id:05d}"


# ---------- RG6 : prix unitaire par défaut ----------

def prix_de_la_ligne(prestation: TypeVetement, prix_demande: int | None) -> int:
    """Le prix négocié s'il est fourni, sinon le prix de base du catalogue."""
    return prestation.prix_base if prix_demande is None else prix_demande


def charger_prestation_active(db: Session, type_vetement_id: int) -> TypeVetement:
    """Une prestation inactive ne peut plus être commandée (422)."""
    prestation = db.get(TypeVetement, type_vetement_id)
    if prestation is None:
        raise ValidationMetierError(f"Prestation {type_vetement_id} inconnue.")
    if not prestation.actif:
        raise ValidationMetierError(
            f"La prestation « {prestation.nom} » n'est plus disponible."
        )
    return prestation


# ---------- RG7 : montants ----------

def somme_prestations(lignes: list[tuple[int, int]]) -> int:
    """lignes = [(quantite, prix_unitaire), ...]"""
    return sum(q * p for q, p in lignes)


def calculer_total(somme: int, remise: int) -> int:
    """total = somme des prestations - remise. La remise ne peut pas la dépasser (422)."""
    if remise > somme:
        raise ValidationMetierError(
            f"La remise ({remise}) ne peut pas dépasser la somme des prestations ({somme})."
        )
    return somme - remise


def verifier_total_vs_paye(total: int, paye: int) -> None:
    """Un changement ne peut jamais ramener le total sous le montant déjà payé (409)."""
    if total < paye:
        raise ConflitError(
            f"Le nouveau total ({total}) serait inférieur au montant déjà payé ({paye})."
        )


# ---------- RG8 : date de livraison prévue ----------

def date_livraison_par_defaut(date_commande: date, delais: list[int]) -> date:
    """Date de commande + le plus long délai des prestations commandées."""
    return date_commande + timedelta(days=max(delais))


def verifier_date_livraison(date_prevue: date, date_commande: date) -> None:
    """Elle ne peut pas précéder la date de commande (422)."""
    if date_prevue < date_commande:
        raise ValidationMetierError(
            "La date de livraison prévue ne peut pas précéder la date de commande."
        )

# ---------- Machine à états (tableau de la section 6) ----------

S = StatutCommande

TRANSITIONS: dict[StatutCommande, set[StatutCommande]] = {
    S.en_attente: {S.en_coupe, S.annulee},
    S.en_coupe: {S.en_couture, S.annulee},
    S.en_couture: {S.essayage, S.terminee, S.annulee},
    S.essayage: {S.retouches, S.terminee, S.annulee},
    S.retouches: {S.essayage, S.terminee, S.annulee},
    S.terminee: {S.livree},   # uniquement par la confirmation de livraison
    S.livree: set(),          # statut final
    S.annulee: set(),         # statut final
}


def statuts_possibles(actuel: StatutCommande) -> list[str]:
    """Statuts atteignables, triés, pour le message d'erreur."""
    return sorted(s.value for s in TRANSITIONS[actuel])


def verifier_transition(
    actuel: StatutCommande,
    demande: StatutCommande,
    role: RoleUtilisateur,
    a_recu_acompte: bool,
    commentaire: str | None,
) -> None:
    """Valide un changement de statut demandé par la route 28.
    Lève l'exception adaptée (403, 409 ou 422), sinon ne renvoie rien."""

    # RG14 : le tailleur ne peut pas annuler (403)
    if demande == S.annulee and role == RoleUtilisateur.tailleur:
        raise InterditError("Le tailleur n'est pas autorisé à annuler une commande.")

    # RG13 : le statut déjà en cours est refusé (409)
    if demande == actuel:
        raise ConflitError(f"La commande est déjà au statut « {actuel.value} ».")

    # RG13 : « livree » ne se pose que par la confirmation de livraison (409)
    if demande == S.livree:
        raise ConflitError(
            "Le statut « livree » ne peut pas être posé ici : "
            "utilisez la confirmation de livraison."
        )

    # Workflow : transition autorisée ?
    if demande not in TRANSITIONS[actuel]:
        possibles = statuts_possibles(actuel)
        suite = ", ".join(possibles) if possibles else "aucun (statut final)"
        raise ConflitError(
            f"Transition interdite : {actuel.value} → {demande.value}. "
            f"Statuts possibles : {suite}"
        )

    # RG14 : annuler une commande avec acompte exige un commentaire (422)
    if demande == S.annulee and a_recu_acompte and not (commentaire and commentaire.strip()):
        raise ValidationMetierError(
            "Un commentaire est obligatoire pour annuler une commande ayant reçu "
            "un acompte (précisez le sort de l'argent : remboursement, avoir...)."
        )

# ---------- RG9 : rattachement des mesures ----------

def resoudre_mesure(db: Session, client_id: int, mesure_id: int | None) -> int | None:
    """Mesure précisée : elle doit appartenir au client (422).
    Sinon : les dernières mesures du client, s'il en a."""
    if mesure_id is not None:
        mesure = db.get(Mesure, mesure_id)
        if mesure is None or mesure.client_id != client_id:
            raise ValidationMetierError(
                "Les mesures indiquées n'appartiennent pas au client de la commande."
            )
        return mesure.id
    derniere = db.scalar(
        select(Mesure).where(Mesure.client_id == client_id)
        .order_by(Mesure.date_prise.desc(), Mesure.id.desc()).limit(1)
    )
    return derniere.id if derniere else None


# ---------- Création (route 24) ----------

def creer(db: Session, data: CommandeCreate, auteur: Utilisateur) -> Commande:
    if db.get(Client, data.client_id) is None:
        raise IntrouvableError(f"Client {data.client_id} introuvable.")

    aujourdhui = date.today()
    mesure_id = resoudre_mesure(db, data.client_id, data.mesure_id)

    # RG6 : prestations actives et prix par défaut
    lignes: list[LigneCommande] = []
    delais: list[int] = []
    for l in data.lignes:
        prestation = charger_prestation_active(db, l.type_vetement_id)
        delais.append(prestation.delai_jours)
        lignes.append(LigneCommande(
            type_vetement_id=prestation.id,
            description=l.description,
            quantite=l.quantite,
            prix_unitaire=prix_de_la_ligne(prestation, l.prix_unitaire),
        ))

    # RG7 : montants calculés par le serveur
    somme = somme_prestations([(l.quantite, l.prix_unitaire) for l in lignes])
    total = calculer_total(somme, data.remise)

    # RG8 : date de livraison prévue
    if data.date_livraison_prevue is not None:
        prevue = data.date_livraison_prevue
        verifier_date_livraison(prevue, aujourdhui)
    else:
        prevue = date_livraison_par_defaut(aujourdhui, delais)

    commande = Commande(
        numero=f"TMP-{id(lignes)}",  # provisoire, remplacé juste après (RG5)
        client_id=data.client_id,
        mesure_id=mesure_id,
        statut=StatutCommande.en_attente,
        date_commande=aujourdhui,
        date_livraison_prevue=prevue,
        remise=data.remise,
        montant_total=total,
        montant_paye=0,
        notes=data.notes,
        cree_par_id=auteur.id,
        lignes=lignes,
    )
    db.add(commande)
    db.flush()  # obtient l'id
    commande.numero = formater_numero(aujourdhui.year, commande.id)  # RG5

    # RG15 : première ligne d'historique (ancien statut vide)
    db.add(HistoriqueStatut(
        commande_id=commande.id,
        ancien_statut=None,
        nouveau_statut=StatutCommande.en_attente,
        commentaire="Création de la commande",
        utilisateur_id=auteur.id,
    ))
    db.flush()
    return commande


# ---------- Lecture ----------

def obtenir(db: Session, commande_id: int) -> Commande:
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise IntrouvableError(f"Commande {commande_id} introuvable.")
    return commande


def vers_detail(commande: Commande) -> dict:
    """Construit un CommandeRead : ajoute client_nom, en_retard, noms de prestations."""
    return {
        "id": commande.id,
        "numero": commande.numero,
        "client_id": commande.client_id,
        "client_nom": f"{commande.client.prenom} {commande.client.nom}",
        "mesure_id": commande.mesure_id,
        "statut": commande.statut,
        "date_commande": commande.date_commande,
        "date_livraison_prevue": commande.date_livraison_prevue,
        "date_livraison_reelle": commande.date_livraison_reelle,
        "remise": commande.remise,
        "montant_total": commande.montant_total,
        "montant_paye": commande.montant_paye,
        "solde": commande.solde,
        "en_retard": est_en_retard(commande),
        "notes": commande.notes,
        "cree_par_id": commande.cree_par_id,
        "created_at": commande.created_at,
        "updated_at": commande.updated_at,
        "lignes": [
            {
                "id": l.id,
                "type_vetement_id": l.type_vetement_id,
                "type_vetement_nom": l.type_vetement.nom,
                "description": l.description,
                "quantite": l.quantite,
                "prix_unitaire": l.prix_unitaire,
                "sous_total": l.sous_total,
            }
            for l in commande.lignes
        ],
        "paiements": commande.paiements,
        "livraison": commande.livraison,
    }


def lister(
    db: Session,
    limit: int,
    offset: int,
    statut: StatutCommande | None = None,
    client_id: int | None = None,
    en_retard: bool | None = None,
    date_min: date | None = None,
    date_max: date | None = None,
    numero: str | None = None,
) -> tuple[list[Commande], int]:
    requete = select(Commande)
    if statut is not None:
        requete = requete.where(Commande.statut == statut)
    if client_id is not None:
        requete = requete.where(Commande.client_id == client_id)
    if date_min is not None:
        requete = requete.where(Commande.date_commande >= date_min)
    if date_max is not None:
        requete = requete.where(Commande.date_commande <= date_max)
    if numero:
        requete = requete.where(Commande.numero.ilike(f"%{numero.strip()}%"))
    if en_retard is not None:
        # RG11 exprimé en SQL
        retard_sql = (Commande.date_livraison_prevue < date.today()) & Commande.statut.not_in(
            [StatutCommande.livree, StatutCommande.annulee]
        )
        requete = requete.where(retard_sql if en_retard else ~retard_sql)

    total = db.scalar(select(func.count()).select_from(requete.subquery()))
    items = db.scalars(
        requete.options(selectinload(Commande.client))
        .order_by(Commande.date_commande.desc(), Commande.id.desc())
        .limit(limit).offset(offset)
    ).all()
    return list(items), total


# ---------- RG12 / RG10 : garde-fous ----------

def verifier_modifiable(commande: Commande) -> None:
    """RG12 : une commande livrée ou annulée n'est plus modifiable (409)."""
    if commande.statut in (StatutCommande.livree, StatutCommande.annulee):
        raise ConflitError(
            f"La commande est « {commande.statut.value} » : elle n'est plus modifiable."
        )


def verifier_lignes_modifiables(commande: Commande) -> None:
    """RG10 : lignes modifiables seulement en « en_attente » (409)."""
    verifier_modifiable(commande)
    if commande.statut != StatutCommande.en_attente:
        raise ConflitError(
            "Les lignes ne sont modifiables que tant que la commande est « en_attente »."
        )


def recalculer_montants(commande: Commande) -> None:
    """RG7 : recalcule le total à partir des lignes et de la remise.
    Refuse (409) un total inférieur au montant déjà payé."""
    somme = somme_prestations([(l.quantite, l.prix_unitaire) for l in commande.lignes])
    total = calculer_total(somme, commande.remise)  # 422 si remise > somme
    verifier_total_vs_paye(total, commande.montant_paye)  # 409
    commande.montant_total = total


# ---------- Route 27 : modification ----------

def modifier(db: Session, commande_id: int, data: CommandeUpdate) -> Commande:
    commande = obtenir(db, commande_id)
    verifier_modifiable(commande)  # RG12
    champs = data.model_dump(exclude_unset=True)

    if "mesure_id" in champs and champs["mesure_id"] is not None:
        commande.mesure_id = resoudre_mesure(db, commande.client_id, champs["mesure_id"])  # RG9

    if "date_livraison_prevue" in champs and champs["date_livraison_prevue"] is not None:
        verifier_date_livraison(champs["date_livraison_prevue"], commande.date_commande)  # RG8
        commande.date_livraison_prevue = champs["date_livraison_prevue"]

    if "notes" in champs:
        commande.notes = champs["notes"]

    if "remise" in champs and champs["remise"] is not None:
        commande.remise = champs["remise"]
        recalculer_montants(commande)  # RG7

    db.flush()
    return commande


# ---------- Routes 30 et 31 : lignes ----------

def ajouter_ligne(db: Session, commande_id: int, data: LigneCommandeCreate) -> Commande:
    commande = obtenir(db, commande_id)
    verifier_lignes_modifiables(commande)  # RG10, RG12
    prestation = charger_prestation_active(db, data.type_vetement_id)  # RG6
    commande.lignes.append(LigneCommande(
        type_vetement_id=prestation.id,
        description=data.description,
        quantite=data.quantite,
        prix_unitaire=prix_de_la_ligne(prestation, data.prix_unitaire),
    ))
    recalculer_montants(commande)
    db.flush()
    return commande


def retirer_ligne(db: Session, commande_id: int, ligne_id: int) -> Commande:
    commande = obtenir(db, commande_id)
    verifier_lignes_modifiables(commande)  # RG10, RG12
    ligne = next((l for l in commande.lignes if l.id == ligne_id), None)
    if ligne is None:
        raise IntrouvableError(f"Ligne {ligne_id} introuvable dans cette commande.")
    if len(commande.lignes) <= 1:
        raise ConflitError("Une commande doit garder au moins une ligne.")  # RG10
    commande.lignes.remove(ligne)  # delete-orphan supprime la ligne
    recalculer_montants(commande)
    db.flush()
    return commande