from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.enums import RoleUtilisateur, StatutCommande
from app.models.utilisateur import Utilisateur
from app.schemas.commande import CommandeCreate, CommandeListe, CommandeRead
from app.schemas.common import Page
from app.services import commandes as service

router = APIRouter(prefix="/commandes", tags=["Commandes"])
accueil = Depends(require_roles(RoleUtilisateur.accueil))  # admin toujours autorisé


@router.post("", response_model=CommandeRead, status_code=status.HTTP_201_CREATED)  # route 24
def creer(data: CommandeCreate, db: Session = Depends(get_db), user: Utilisateur = accueil):
    commande = service.creer(db, data, user)
    db.commit()
    return service.vers_detail(commande)


@router.get("", response_model=Page[CommandeListe])  # route 25
def lister(
    statut: StatutCommande | None = None,
    client_id: int | None = None,
    en_retard: bool | None = None,
    date_min: date | None = None,
    date_max: date | None = None,
    numero: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    items, total = service.lister(
        db, limit, offset, statut, client_id, en_retard, date_min, date_max, numero
    )
    return Page[CommandeListe](
        items=[service.vers_liste(c) for c in items],
        total=total, limit=limit, offset=offset,
    )


@router.get("/{commande_id}", response_model=CommandeRead)  # route 26
def detail(commande_id: int, db: Session = Depends(get_db),
           _: Utilisateur = Depends(get_current_user)):
    return service.vers_detail(service.obtenir(db, commande_id))