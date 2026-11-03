from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.enums import RoleUtilisateur
from app.models.utilisateur import Utilisateur
from app.schemas.mesure import MesureCreate, MesureRead, MesureUpdate
from app.services import mesures as service

# Admin toujours autorisé en plus du tailleur (voir require_roles)
tailleur = Depends(require_roles(RoleUtilisateur.tailleur))

router_client = APIRouter(prefix="/clients/{client_id}/mesures", tags=["Mesures"])
router = APIRouter(prefix="/mesures", tags=["Mesures"])


@router_client.post("", response_model=MesureRead, status_code=status.HTTP_201_CREATED)  # route 18
def creer(client_id: int, data: MesureCreate, db: Session = Depends(get_db),
          user: Utilisateur = tailleur):
    mesure = service.creer(db, client_id, data, user)
    db.commit()
    return mesure


@router_client.get("", response_model=list[MesureRead])  # route 19
def historique(client_id: int, db: Session = Depends(get_db),
               _: Utilisateur = Depends(get_current_user)):
    return service.historique(db, client_id)


@router_client.get("/derniere", response_model=MesureRead)  # route 20
def derniere(client_id: int, db: Session = Depends(get_db),
             _: Utilisateur = Depends(get_current_user)):
    return service.derniere(db, client_id)


@router.get("/{mesure_id}", response_model=MesureRead)  # route 21
def detail(mesure_id: int, db: Session = Depends(get_db),
           _: Utilisateur = Depends(get_current_user)):
    return service.obtenir(db, mesure_id)


@router.patch("/{mesure_id}", response_model=MesureRead)  # route 22
def modifier(mesure_id: int, data: MesureUpdate, db: Session = Depends(get_db),
             _: Utilisateur = tailleur):
    mesure = service.modifier(db, mesure_id, data)
    db.commit()
    return mesure


@router.delete("/{mesure_id}", status_code=status.HTTP_204_NO_CONTENT)  # route 23
def supprimer(mesure_id: int, db: Session = Depends(get_db), _: Utilisateur = tailleur):
    service.supprimer(db, mesure_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)