from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import NonAuthentifieError
from app.models.utilisateur import Utilisateur
from app.security import create_access_token, verify_password

# RG23 : un seul message, que l'email soit inconnu ou le mot de passe faux
MESSAGE_ECHEC = "Identifiants incorrects."


def authentifier(db: Session, email: str, mot_de_passe: str) -> tuple[str, int]:
    """Vérifie les identifiants et renvoie (jeton, expires_in), sinon 401."""
    user = db.scalar(select(Utilisateur).where(Utilisateur.email == email.lower()))

    if user is None or not verify_password(mot_de_passe, user.mot_de_passe_hash):
        raise NonAuthentifieError(MESSAGE_ECHEC)
    if not user.actif:
        # même message : on ne révèle pas l'existence du compte
        raise NonAuthentifieError(MESSAGE_ECHEC)

    return create_access_token(user.id)