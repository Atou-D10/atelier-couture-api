from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import ValidationMetierError
from app.models.client import Client
from app.models.commande import Commande
from app.models.enums import StatutCommande
from app.models.ligne_commande import LigneCommande
from app.models.livraison import Livraison
from app.models.paiement import Paiement
from app.models.type_vetement import TypeVetement
from app.schemas.statistiques import Granularite
from app.services.commandes import vers_liste

NON_ANNULEE = Commande.statut != StatutCommande.annulee


def _debut_mois(d: date) -> date:
    return d.replace(day=1)


def _somme(db: Session, colonne, *filtres) -> int:
    return int(db.scalar(select(func.coalesce(func.sum(colonne), 0)).where(*filtres)))


# ---------- Route 39 ----------

def tableau_de_bord(db: Session) -> dict:
    auj = date.today()
    debut = _debut_mois(auj)

    ca_mois = _somme(db, Commande.montant_total, NON_ANNULEE, Commande.date_commande >= debut,
                     Commande.date_commande <= auj)
    encaisse_mois = _somme(db, Paiement.montant, Paiement.date_paiement >= debut,
                           Paiement.date_paiement <= auj)
    nb_mois = db.scalar(select(func.count()).where(
        NON_ANNULEE, Commande.date_commande >= debut, Commande.date_commande <= auj))
    reste = _somme(db, Commande.montant_total - Commande.montant_paye, NON_ANNULEE)

    # Tous les statuts présents, même à 0
    par_statut = {s: 0 for s in StatutCommande}
    for statut, n in db.execute(select(Commande.statut, func.count()).group_by(Commande.statut)):
        par_statut[statut] = n

    nb_retard = db.scalar(select(func.count()).where(
        Commande.date_livraison_prevue < auj,
        Commande.statut.not_in([StatutCommande.livree, StatutCommande.annulee])))
    livraisons_jour = db.scalar(select(func.count()).where(Livraison.date_prevue == auj))

    return {
        "chiffre_affaires_mois": ca_mois,
        "encaisse_mois": encaisse_mois,
        "nb_commandes_mois": nb_mois,
        "reste_a_encaisser": reste,
        "commandes_par_statut": par_statut,
        "nb_commandes_en_retard": nb_retard,
        "commandes_pretes_a_livrer": par_statut[StatutCommande.terminee],
        "livraisons_du_jour": livraisons_jour,
    }


# ---------- Route 40 ----------

def _periode(colonne, granularite: Granularite):
    fmt = "YYYY-MM-DD" if granularite == Granularite.jour else "YYYY-MM"
    return func.to_char(colonne, fmt)


def chiffre_affaires(db: Session, granularite: Granularite,
                     date_debut: date | None, date_fin: date | None) -> dict:
    auj = date.today()
    date_debut = date_debut or _debut_mois(auj)
    date_fin = date_fin or auj
    if date_debut > date_fin:
        raise ValidationMetierError("date_debut ne peut pas être postérieure à date_fin.")

    p_cmd = _periode(Commande.date_commande, granularite)
    ca = dict(db.execute(
        select(p_cmd, func.sum(Commande.montant_total))
        .where(NON_ANNULEE, Commande.date_commande.between(date_debut, date_fin))
        .group_by(p_cmd)
    ).all())

    p_pay = _periode(Paiement.date_paiement, granularite)
    enc = dict(db.execute(
        select(p_pay, func.sum(Paiement.montant))
        .where(Paiement.date_paiement.between(date_debut, date_fin))
        .group_by(p_pay)
    ).all())

    # Seules les périodes avec activité sont listées
    points = [
        {"periode": p, "chiffre_affaires": int(ca.get(p, 0)), "encaisse": int(enc.get(p, 0))}
        for p in sorted(set(ca) | set(enc))
    ]
    return {"granularite": granularite, "date_debut": date_debut, "date_fin": date_fin,
            "points": points}


# ---------- Route 41 ----------

def par_type_vetement(db: Session, date_debut: date | None, date_fin: date | None) -> list[dict]:
    date_debut = date_debut or _debut_mois(date.today())
    date_fin = date_fin or date.today()
    ca = func.sum(LigneCommande.quantite * LigneCommande.prix_unitaire)
    lignes = db.execute(
        select(TypeVetement.id, TypeVetement.nom,
               func.sum(LigneCommande.quantite), ca)
        .join(LigneCommande, LigneCommande.type_vetement_id == TypeVetement.id)
        .join(Commande, Commande.id == LigneCommande.commande_id)
        .where(NON_ANNULEE, Commande.date_commande.between(date_debut, date_fin))
        .group_by(TypeVetement.id, TypeVetement.nom)
        .order_by(ca.desc())
    ).all()
    return [{"type_vetement_id": i, "nom": n, "quantite_vendue": int(q),
             "chiffre_affaires": int(c)} for i, n, q, c in lignes]


# ---------- Route 42 ----------

def top_clients(db: Session, date_debut: date | None, date_fin: date | None,
                limite: int) -> list[dict]:
    date_debut = date_debut or _debut_mois(date.today())
    date_fin = date_fin or date.today()
    ca = func.sum(Commande.montant_total)
    lignes = db.execute(
        select(Client.id, Client.nom, Client.prenom, func.count(Commande.id), ca,
               func.sum(Commande.montant_total - Commande.montant_paye))
        .join(Commande, Commande.client_id == Client.id)
        .where(NON_ANNULEE, Commande.date_commande.between(date_debut, date_fin))
        .group_by(Client.id, Client.nom, Client.prenom)
        .order_by(ca.desc())
        .limit(limite)
    ).all()
    return [{"client_id": i, "nom": n, "prenom": p, "nb_commandes": nb,
             "chiffre_affaires": int(c), "solde_du": int(s)} for i, n, p, nb, c, s in lignes]


# ---------- Route 43 ----------

def impayes(db: Session, limit: int, offset: int) -> tuple[list[dict], int]:
    base = select(Commande).where(NON_ANNULEE, Commande.montant_total - Commande.montant_paye > 0)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    items = db.scalars(
        base.order_by(Commande.date_livraison_prevue, Commande.id).limit(limit).offset(offset)
    ).all()
    return [vers_liste(c) for c in items], total