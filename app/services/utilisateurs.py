from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ConflitError, IntrouvableError
from app.models.enums import RoleUtilisateur
from app.models.utilisateur import Utilisateur
from app.schemas.utilisateur import UtilisateurCreate, UtilisateurUpdate
from app.security import hash_password


def creer(db: Session, data: UtilisateurCreate) -> Utilisateur:
    email = data.email.lower()  # emails toujours en minuscules (cohérent avec le login)
    if db.scalar(select(Utilisateur).where(Utilisateur.email == email)):
        raise ConflitError(f"Un compte existe déjà avec l'e-mail {email}.")

    user = Utilisateur(
        email=email,
        nom_complet=data.nom_complet,
        mot_de_passe_hash=hash_password(data.mot_de_passe),  # jamais en clair
        role=data.role,
        actif=True,
    )
    db.add(user)
    db.flush()  # obtient l'id sans valider : le commit est fait par le routeur
    return user


def lister(db: Session) -> list[Utilisateur]:
    return list(db.scalars(select(Utilisateur).order_by(Utilisateur.nom_complet)))


def obtenir(db: Session, user_id: int) -> Utilisateur:
    user = db.get(Utilisateur, user_id)
    if user is None:
        raise IntrouvableError(f"Utilisateur {user_id} introuvable.")
    return user


def modifier(
    db: Session, user_id: int, data: UtilisateurUpdate, courant: Utilisateur
) -> Utilisateur:
    user = obtenir(db, user_id)
    champs = data.model_dump(exclude_unset=True)  # seulement les champs envoyés

    # RG24 : un admin ne peut ni se désactiver ni se retirer son rôle admin
    if user.id == courant.id:
        if champs.get("actif") is False:
            raise ConflitError("Vous ne pouvez pas désactiver votre propre compte.")
        if "role" in champs and champs["role"] != RoleUtilisateur.admin:
            raise ConflitError("Vous ne pouvez pas retirer votre propre rôle d'administrateur.")

    if "mot_de_passe" in champs:
        mdp = champs.pop("mot_de_passe")
        if mdp is not None:
            user.mot_de_passe_hash = hash_password(mdp)

    # nom_complet, role et actif ne sont pas annulables
    for cle, valeur in champs.items():
        if valeur is None:
            continue
        setattr(user, cle, valeur)

    db.flush()
    return user