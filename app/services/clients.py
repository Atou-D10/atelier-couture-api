from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.exceptions import ConflitError, IntrouvableError, ValidationMetierError
from app.models.client import Client
from app.models.commande import Commande
from app.models.enums import GenreClient, StatutCommande
from app.models.mesure import Mesure
from app.schemas.client import ClientCreate, ClientUpdate, normaliser_telephone


def _verifier_telephone_libre(db: Session, telephone: str, ignorer_id: int | None = None):
    """RG1 : le téléphone est unique, doublon -> 409."""
    requete = select(Client).where(Client.telephone == telephone)
    if ignorer_id is not None:
        requete = requete.where(Client.id != ignorer_id)  # garder son propre numéro est permis
    if db.scalar(requete):
        raise ConflitError(f"Un client existe déjà avec le téléphone {telephone}.")


def creer(db: Session, data: ClientCreate) -> Client:
    _verifier_telephone_libre(db, data.telephone)  # déjà normalisé par Pydantic
    client = Client(**data.model_dump())
    db.add(client)
    db.flush()
    return client


def obtenir(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise IntrouvableError(f"Client {client_id} introuvable.")
    return client


def lister(
    db: Session, q: str | None, genre: GenreClient | None, limit: int, offset: int
) -> tuple[list[Client], int]:
    requete = select(Client)
    if q is not None:
        q = q.strip()
        if len(q) < 2:
            raise ValidationMetierError("La recherche doit contenir au moins 2 caractères.")
        motif = f"%{q}%"
        # Pour le téléphone, on cherche aussi la version normalisée (ex. "77 123")
        tel = q.replace(" ", "").replace(".", "").replace("-", "")
        requete = requete.where(
            or_(
                Client.nom.ilike(motif),
                Client.prenom.ilike(motif),
                Client.telephone.ilike(f"%{tel}%"),
            )
        )
    if genre is not None:
        requete = requete.where(Client.genre == genre)

    total = db.scalar(select(func.count()).select_from(requete.subquery()))
    items = db.scalars(
        requete.order_by(Client.nom, Client.prenom).limit(limit).offset(offset)
    ).all()
    return list(items), total


def modifier(db: Session, client_id: int, data: ClientUpdate) -> Client:
    client = obtenir(db, client_id)
    champs = data.model_dump(exclude_unset=True)  # PATCH : seulement ce qui est envoyé

    if "telephone" in champs:
        _verifier_telephone_libre(db, champs["telephone"], ignorer_id=client.id)

    for cle, valeur in champs.items():
        setattr(client, cle, valeur)
    db.flush()
    return client


def supprimer(db: Session, client_id: int) -> None:
    client = obtenir(db, client_id)
    # RG4 : un client qui a des commandes ne peut pas être supprimé
    nb = db.scalar(select(func.count()).where(Commande.client_id == client.id))
    if nb:
        raise ConflitError(
            f"Suppression impossible : ce client a {nb} commande(s)."
        )
    db.delete(client)  # supprime aussi ses mesures (cascade)
    db.flush()


def commandes_du_client(
    db: Session, client_id: int, limit: int, offset: int
) -> tuple[list[Commande], int]:
    obtenir(db, client_id)  # 404 si inconnu
    base = select(Commande).where(Commande.client_id == client_id)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    items = db.scalars(
        base.order_by(Commande.date_commande.desc(), Commande.id.desc())
        .limit(limit).offset(offset)
    ).all()
    return list(items), total


def resume(db: Session, client_id: int) -> dict:
    obtenir(db, client_id)
    # Les commandes annulées sont exclues
    ligne = db.execute(
        select(
            func.count(Commande.id),
            func.coalesce(func.sum(Commande.montant_total), 0),
            func.coalesce(func.sum(Commande.montant_paye), 0),
            func.max(Commande.date_commande),
        ).where(
            Commande.client_id == client_id,
            Commande.statut != StatutCommande.annulee,
        )
    ).one()
    nb, ca, paye, derniere = ligne
    a_des_mesures = db.scalar(
        select(func.count()).where(Mesure.client_id == client_id)
    ) > 0
    return {
        "nb_commandes": nb,
        "chiffre_affaires": int(ca),
        "total_paye": int(paye),
        "solde_du": int(ca) - int(paye),
        "derniere_commande": derniere,
        "a_des_mesures": a_des_mesures,
    }