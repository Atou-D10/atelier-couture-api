from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.enums import GenreClient
from app.models.utilisateur import Utilisateur
from app.schemas.client import ClientCreate, ClientRead, ClientResume, ClientUpdate
from app.schemas.commande import CommandeListe
from app.schemas.common import Page
from app.services import clients as service
from app.services import commandes as commandes_service

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)  # route 7
def creer(
    data: ClientCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),  # tous les rôles
):
    client = service.creer(db, data)
    db.commit()
    return client


@router.get("", response_model=Page[ClientRead])  # route 8
def lister(
    q: str | None = Query(default=None, description="Nom, prénom ou téléphone (2 car. min)"),
    genre: GenreClient | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    items, total = service.lister(db, q, genre, limit, offset)
    return Page[ClientRead](items=items, total=total, limit=limit, offset=offset)


@router.get("/{client_id}", response_model=ClientRead)  # route 9
def detail(
    client_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    return service.obtenir(db, client_id)


@router.patch("/{client_id}", response_model=ClientRead)  # route 10
def modifier(
    client_id: int,
    data: ClientUpdate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    client = service.modifier(db, client_id, data)
    db.commit()
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)  # route 11
def supprimer(
    client_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_roles()),  # admin seul
):
    service.supprimer(db, client_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{client_id}/commandes", response_model=Page[CommandeListe])  # route 12
def commandes_du_client(
    client_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    items, total = service.commandes_du_client(db, client_id, limit, offset)
    return Page[CommandeListe](
        items=[commandes_service.vers_liste(c) for c in items],
        total=total, limit=limit, offset=offset,
    )


@router.get("/{client_id}/resume", response_model=ClientResume)  # route 13
def resume(
    client_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    return service.resume(db, client_id)