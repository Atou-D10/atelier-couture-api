from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models.utilisateur import Utilisateur
from app.schemas.utilisateur import UtilisateurCreate, UtilisateurRead, UtilisateurUpdate
from app.services import utilisateurs as service

# require_roles() sans argument = admin seul
router = APIRouter(
    prefix="/utilisateurs",
    tags=["Utilisateurs"],
)
admin_seul = Depends(require_roles())


@router.post("", response_model=UtilisateurRead, status_code=status.HTTP_201_CREATED)  # route 3
def creer(
    data: UtilisateurCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = admin_seul,
):
    user = service.creer(db, data)
    db.commit()
    return user


@router.get("", response_model=list[UtilisateurRead])  # route 4
def lister(db: Session = Depends(get_db), _: Utilisateur = admin_seul):
    return service.lister(db)


@router.get("/{user_id}", response_model=UtilisateurRead)  # route 5
def detail(user_id: int, db: Session = Depends(get_db), _: Utilisateur = admin_seul):
    return service.obtenir(db, user_id)


@router.patch("/{user_id}", response_model=UtilisateurRead)  # route 6
def modifier(
    user_id: int,
    data: UtilisateurUpdate,
    db: Session = Depends(get_db),
    courant: Utilisateur = admin_seul,
):
    user = service.modifier(db, user_id, data, courant)
    db.commit()
    return user