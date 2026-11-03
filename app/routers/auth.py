from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.utilisateur import Utilisateur
from app.schemas.auth import Token
from app.schemas.utilisateur import UtilisateurRead
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=Token)  # route 1
def login(
    form: OAuth2PasswordRequestForm = Depends(),  # username = email, password
    db: Session = Depends(get_db),
):
    token, expires_in = auth_service.authentifier(db, form.username, form.password)
    return Token(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UtilisateurRead)  # route 2
def me(user: Utilisateur = Depends(get_current_user)):
    return user  # UtilisateurRead filtre : jamais de mot de passe