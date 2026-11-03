from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import InterditError, NonAuthentifieError
from app.models.enums import RoleUtilisateur
from app.models.utilisateur import Utilisateur
from app.security import decode_access_token

# auto_error=False : c'est NOUS qui levons le 401 (format {"detail": ...} en français).
# tokenUrl : adresse du login, utilisée par le bouton "Authorize" de Swagger.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Utilisateur:
    """Renvoie l'utilisateur connecté, sinon 401."""
    if token is None:
        raise NonAuthentifieError("Authentification requise : jeton manquant.")

    user_id = decode_access_token(token)
    if user_id is None:
        raise NonAuthentifieError("Jeton invalide ou expiré.")

    user = db.get(Utilisateur, user_id)
    # RG22 : l'état "actif" est vérifié en base à CHAQUE requête
    if user is None or not user.actif:
        raise NonAuthentifieError("Compte inexistant ou désactivé.")

    return user


def require_roles(*roles: RoleUtilisateur):
    """Fabrique une dépendance qui exige l'un des rôles donnés (sinon 403).
    L'admin est toujours autorisé (section 4 de l'énoncé)."""
    autorises = set(roles) | {RoleUtilisateur.admin}

    def verifier(user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
        if user.role not in autorises:
            raise InterditError("Droits insuffisants pour cette action.")
        return user

    return verifier