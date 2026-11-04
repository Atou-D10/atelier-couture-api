from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import ConflitError, IntrouvableError, ValidationMetierError
from app.models.commande import Commande
from app.models.enums import StatutCommande
from app.models.paiement import Paiement
from app.models.utilisateur import Utilisateur
from app.schemas.paiement import PaiementCreate


def _commande(db: Session, commande_id: int) -> Commande:
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise IntrouvableError(f"Commande {commande_id} introuvable.")
    return commande


def recalculer_paye(db: Session, commande: Commande) -> None:
    """RG7/RG17 : payé = somme des paiements."""
    db.flush()
    commande.montant_paye = int(db.scalar(
        select(func.coalesce(func.sum(Paiement.montant), 0))
        .where(Paiement.commande_id == commande.id)
    ))


def verifier_paiement(commande: Commande, montant: int, date_paiement: date, aujourdhui: date) -> None:
    """RG16 (le montant > 0 est déjà garanti par Pydantic)."""
    if commande.statut == StatutCommande.annulee:
        raise ConflitError("Paiement refusé : la commande est annulée.")
    if date_paiement > aujourdhui:
        raise ValidationMetierError("La date de paiement ne peut pas être dans le futur.")
    if montant > commande.solde:
        raise ConflitError(
            f"Le paiement ({montant}) dépasse le solde restant ({commande.solde})."
        )


def encaisser(db: Session, commande_id: int, data: PaiementCreate, auteur: Utilisateur) -> Paiement:
    commande = _commande(db, commande_id)
    aujourdhui = date.today()
    date_paiement = data.date_paiement or aujourdhui
    verifier_paiement(commande, data.montant, date_paiement, aujourdhui)

    paiement = Paiement(
        commande_id=commande.id, montant=data.montant, mode=data.mode,
        reference=data.reference, date_paiement=date_paiement,
        enregistre_par_id=auteur.id,
    )
    db.add(paiement)
    recalculer_paye(db, commande)
    return paiement


def lister(db: Session, commande_id: int) -> list[Paiement]:
    _commande(db, commande_id)
    return list(db.scalars(
        select(Paiement).where(Paiement.commande_id == commande_id).order_by(Paiement.id)
    ))


def annuler(db: Session, paiement_id: int) -> None:
    """RG17 : supprime le paiement et recalcule le payé (donc le solde)."""
    paiement = db.get(Paiement, paiement_id)
    if paiement is None:
        raise IntrouvableError(f"Paiement {paiement_id} introuvable.")
    commande = _commande(db, paiement.commande_id)
    db.delete(paiement)
    recalculer_paye(db, commande)