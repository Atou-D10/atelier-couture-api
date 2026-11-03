from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.utilisateur import Utilisateur
from app.schemas.type_vetement import (
    TypeVetementCreate,
    TypeVetementRead,
    TypeVetementUpdate,
)
from app.services import catalogue as service

router = APIRouter(prefix="/catalogue", tags=["Catalogue"])


@router.post("", response_model=TypeVetementRead, status_code=status.HTTP_201_CREATED)  # route 14
def creer(
    data: TypeVetementCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_roles()),  # admin seul
):
    prestation = service.creer(db, data)
    db.commit()
    return prestation


@router.get("", response_model=list[TypeVetementRead])  # route 15
def lister(
    actifs_seulement: bool = True,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    return service.lister(db, actifs_seulement)


@router.get("/{type_id}", response_model=TypeVetementRead)  # route 16
def detail(
    type_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    return service.obtenir(db, type_id)


@router.patch("/{type_id}", response_model=TypeVetementRead)  # route 17
def modifier(
    type_id: int,
    data: TypeVetementUpdate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_roles()),  # admin seul
):
    prestation = service.modifier(db, type_id, data)
    db.commit()
    return prestation