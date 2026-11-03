from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import settings

# ---------- Mots de passe (RG21) ----------

_hasher = PasswordHasher()  # Argon2id avec des paramètres sûrs par défaut


def hash_password(mot_de_passe: str) -> str:
    """Renvoie le hash à stocker en base (jamais le mot de passe en clair)."""
    return _hasher.hash(mot_de_passe)


def verify_password(mot_de_passe: str, hash_stocke: str) -> bool:
    """True si le mot de passe correspond au hash, False sinon."""
    try:
        return _hasher.verify(hash_stocke, mot_de_passe)
    except (VerificationError, InvalidHashError):
        return False


# ---------- Jetons JWT (RG22) ----------

def create_access_token(user_id: int) -> tuple[str, int]:
    """Crée un jeton signé. Renvoie (jeton, durée de validité en secondes)."""
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    payload = {
        "sub": str(user_id),  # "sub" = sujet du jeton (l'utilisateur)
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expires_in


def decode_access_token(token: str) -> int | None:
    """Renvoie l'id utilisateur si le jeton est valide, None sinon
    (signature fausse, jeton modifié, expiré, mal formé)."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None