from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ConflitError, IntrouvableError
from app.models.type_vetement import TypeVetement
from app.schemas.type_vetement import TypeVetementCreate, TypeVetementUpdate


def _verifier_nom_libre(db: Session, nom: str, ignorer_id: int | None = None):
    """Le nom d'une prestation est unique (409)."""
    requete = select(TypeVetement).where(TypeVetement.nom == nom)
    if ignorer_id is not None:
        requete = requete.where(TypeVetement.id != ignorer_id)
    if db.scalar(requete):
        raise ConflitError(f"Une prestation nommée « {nom} » existe déjà.")


def creer(db: Session, data: TypeVetementCreate) -> TypeVetement:
    _verifier_nom_libre(db, data.nom)
    prestation = TypeVetement(**data.model_dump(), actif=True)
    db.add(prestation)
    db.flush()
    return prestation


def lister(db: Session, actifs_seulement: bool) -> list[TypeVetement]:
    requete = select(TypeVetement)
    if actifs_seulement:
        requete = requete.where(TypeVetement.actif.is_(True))
    return list(db.scalars(requete.order_by(TypeVetement.nom)))


def obtenir(db: Session, type_id: int) -> TypeVetement:
    prestation = db.get(TypeVetement, type_id)
    if prestation is None:
        raise IntrouvableError(f"Prestation {type_id} introuvable.")
    return prestation


def modifier(db: Session, type_id: int, data: TypeVetementUpdate) -> TypeVetement:
    prestation = obtenir(db, type_id)
    champs = data.model_dump(exclude_unset=True)  # PATCH partiel

    if "nom" in champs and champs["nom"] is not None:
        _verifier_nom_libre(db, champs["nom"], ignorer_id=prestation.id)

    for cle, valeur in champs.items():
        if valeur is None and cle != "description":
            continue  # nom, prix, délai et actif ne sont pas annulables
        setattr(prestation, cle, valeur)
    db.flush()
    return prestation