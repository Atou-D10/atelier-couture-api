from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models.utilisateur import Utilisateur
from app.schemas.commande import CommandeListe
from app.schemas.common import Page
from app.schemas.statistiques import (
    ChiffreAffairesPeriode, Granularite, StatTopClient, StatTypeVetement, TableauDeBord,
)
from app.services import statistiques as service

router = APIRouter(prefix="/statistiques", tags=["Statistiques"])
admin = Depends(require_roles())  # admin seul


@router.get("/tableau-de-bord", response_model=TableauDeBord)  # route 39
def tableau_de_bord(db: Session = Depends(get_db), _: Utilisateur = admin):
    return service.tableau_de_bord(db)


@router.get("/chiffre-affaires", response_model=ChiffreAffairesPeriode)  # route 40
def chiffre_affaires(granularite: Granularite = Granularite.jour,
                     date_debut: date | None = None, date_fin: date | None = None,
                     db: Session = Depends(get_db), _: Utilisateur = admin):
    return service.chiffre_affaires(db, granularite, date_debut, date_fin)


@router.get("/types-vetement", response_model=list[StatTypeVetement])  # route 41
def types_vetement(date_debut: date | None = None, date_fin: date | None = None,
                   db: Session = Depends(get_db), _: Utilisateur = admin):
    return service.par_type_vetement(db, date_debut, date_fin)


@router.get("/top-clients", response_model=list[StatTopClient])  # route 42
def top_clients(date_debut: date | None = None, date_fin: date | None = None,
                limite: int = Query(default=10, ge=1, le=100),
                db: Session = Depends(get_db), _: Utilisateur = admin):
    return service.top_clients(db, date_debut, date_fin, limite)


@router.get("/impayes", response_model=Page[CommandeListe])  # route 43
def impayes(limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0),
            db: Session = Depends(get_db), _: Utilisateur = admin):
    items, total = service.impayes(db, limit, offset)
    return Page[CommandeListe](items=items, total=total, limit=limit, offset=offset)