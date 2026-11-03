from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import ConflitError, IntrouvableError, ValidationMetierError
from app.models.client import Client
from app.models.commande import Commande
from app.models.mesure import CHAMPS_MESURES, Mesure
from app.models.utilisateur import Utilisateur
from app.schemas.mesure import MesureCreate, MesureUpdate


def _client_existe(db: Session, client_id: int) -> None:
    if db.get(Client, client_id) is None:
        raise IntrouvableError(f"Client {client_id} introuvable.")


def creer(db: Session, client_id: int, data: MesureCreate, tailleur: Utilisateur) -> Mesure:
    _client_existe(db, client_id)
    champs = data.model_dump()
    # date_prise absente -> aujourd'hui
    champs["date_prise"] = champs["date_prise"] or date.today()
    mesure = Mesure(client_id=client_id, prise_par_id=tailleur.id, **champs)
    db.add(mesure)
    db.flush()
    return mesure


def historique(db: Session, client_id: int) -> list[Mesure]:
    """RG3 : tout l'historique, la plus récente d'abord."""
    _client_existe(db, client_id)
    return list(db.scalars(
        select(Mesure).where(Mesure.client_id == client_id)
        .order_by(Mesure.date_prise.desc(), Mesure.id.desc())
    ))


def derniere(db: Session, client_id: int) -> Mesure:
    """RG3 : les dernières mesures = la prise de date la plus récente."""
    _client_existe(db, client_id)
    mesure = db.scalar(
        select(Mesure).where(Mesure.client_id == client_id)
        .order_by(Mesure.date_prise.desc(), Mesure.id.desc()).limit(1)
    )
    if mesure is None:
        raise IntrouvableError("Ce client n'a aucune prise de mesures.")
    return mesure


def obtenir(db: Session, mesure_id: int) -> Mesure:
    mesure = db.get(Mesure, mesure_id)
    if mesure is None:
        raise IntrouvableError(f"Prise de mesures {mesure_id} introuvable.")
    return mesure


def modifier(db: Session, mesure_id: int, data: MesureUpdate) -> Mesure:
    mesure = obtenir(db, mesure_id)
    champs = data.model_dump(exclude_unset=True)  # PATCH partiel

    # date_prise est obligatoire en base : on ignore un null
    if "date_prise" in champs and champs["date_prise"] is None:
        del champs["date_prise"]

    for cle, valeur in champs.items():
        setattr(mesure, cle, valeur)  # une mesure envoyée à null est effacée

    # RG2 : après correction, il doit rester au moins une mesure
    if all(getattr(mesure, c) is None for c in CHAMPS_MESURES):
        db.rollback()
        raise ValidationMetierError("Une prise de mesures doit contenir au moins une mesure.")

    db.flush()
    return mesure


def supprimer(db: Session, mesure_id: int) -> None:
    mesure = obtenir(db, mesure_id)
    # RG4 : mesures utilisées par une commande -> 409
    nb = db.scalar(select(func.count()).where(Commande.mesure_id == mesure.id))
    if nb:
        raise ConflitError(f"Suppression impossible : ces mesures sont utilisées par {nb} commande(s).")
    db.delete(mesure)
    db.flush()