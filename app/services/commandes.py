from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.commande import Commande
from app.models.enums import StatutCommande

from app.exceptions import ConflitError, ValidationMetierError
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