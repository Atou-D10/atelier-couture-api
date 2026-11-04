from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.enums import RoleUtilisateur, StatutLivraison
from app.models.utilisateur import Utilisateur
from app.schemas.commande import CommandeRead
from app.schemas.livraison import (
    LivraisonConfirmer, LivraisonListe, LivraisonPlanifier, LivraisonRead,
)
from app.services import commandes as commandes_service
from app.services import livraisons as service

router_commande = APIRouter(prefix="/commandes/{commande_id}/livraison", tags=["Livraisons"])
router = APIRouter(prefix="/livraisons", tags=["Livraisons"])
accueil = Depends(require_roles(RoleUtilisateur.accueil))


@router_commande.put("", response_model=LivraisonRead)  # route 35
def planifier(commande_id: int, data: LivraisonPlanifier, db: Session = Depends(get_db),
              _: Utilisateur = accueil):
    livraison = service.planifier(db, commande_id, data)
    db.commit()
    return livraison


@router_commande.get("", response_model=LivraisonRead)  # route 36
def detail(commande_id: int, db: Session = Depends(get_db),
           _: Utilisateur = Depends(get_current_user)):
    return service.obtenir(db, commande_id)


@router_commande.post("/confirmer", response_model=CommandeRead)  # route 37
def confirmer(commande_id: int, data: LivraisonConfirmer | None = None,
              db: Session = Depends(get_db), user: Utilisateur = accueil):
    commande = service.confirmer(db, commande_id, data or LivraisonConfirmer(), user)
    db.commit()
    return commandes_service.vers_detail(commande)


@router.get("", response_model=list[LivraisonListe])  # route 38
def lister(statut: StatutLivraison | None = None, date_min: date | None = None,
           date_max: date | None = None, db: Session = Depends(get_db),
           _: Utilisateur = Depends(get_current_user)):
    return service.lister(db, statut, date_min, date_max)