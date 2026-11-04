from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.enums import RoleUtilisateur
from app.models.utilisateur import Utilisateur
from app.schemas.paiement import PaiementCreate, PaiementRead
from app.services import paiements as service

router_commande = APIRouter(prefix="/commandes/{commande_id}/paiements", tags=["Paiements"])
router = APIRouter(prefix="/paiements", tags=["Paiements"])


@router_commande.post("", response_model=PaiementRead, status_code=status.HTTP_201_CREATED)  # route 32
def encaisser(commande_id: int, data: PaiementCreate, db: Session = Depends(get_db),
              user: Utilisateur = Depends(require_roles(RoleUtilisateur.accueil))):
    paiement = service.encaisser(db, commande_id, data, user)
    db.commit()
    return paiement


@router_commande.get("", response_model=list[PaiementRead])  # route 33
def lister(commande_id: int, db: Session = Depends(get_db),
           _: Utilisateur = Depends(get_current_user)):
    return service.lister(db, commande_id)


@router.delete("/{paiement_id}", status_code=status.HTTP_204_NO_CONTENT)  # route 34
def annuler(paiement_id: int, db: Session = Depends(get_db),
            _: Utilisateur = Depends(require_roles())):  # admin seul
    service.annuler(db, paiement_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)