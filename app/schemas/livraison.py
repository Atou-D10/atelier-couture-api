from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ModeLivraison, StatutLivraison


class LivraisonPlanifier(BaseModel):
    """Route 35 (PUT). L'adresse obligatoire pour 'domicile' est vérifiée
    par le service (RG18, 422)."""

    mode: ModeLivraison
    date_prevue: date
    adresse: str | None = Field(default=None, max_length=255)
    livreur: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class LivraisonConfirmer(BaseModel):
    """Route 37 : corps facultatif (RG19-20)."""

    date_effective: date | None = None
    autoriser_solde_impaye: bool = False


class LivraisonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commande_id: int
    mode: ModeLivraison
    adresse: str | None
    livreur: str | None
    date_prevue: date
    date_effective: date | None
    statut: StatutLivraison
    notes: str | None


class LivraisonListe(BaseModel):
    """Route 38 : élément de la tournée."""

    id: int
    commande_id: int
    numero_commande: str
    client_nom: str
    client_telephone: str
    solde_commande: int
    mode: ModeLivraison
    adresse: str | None
    livreur: str | None
    date_prevue: date
    date_effective: date | None
    statut: StatutLivraison