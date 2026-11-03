from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatutCommande
from app.schemas.livraison import LivraisonRead
from app.schemas.paiement import PaiementRead


# ---------- Lignes ----------

class LigneCommandeCreate(BaseModel):
    """Une prestation commandée. prix_unitaire absent = prix du catalogue (RG6)."""

    type_vetement_id: int
    description: str | None = Field(default=None, max_length=255)
    quantite: int = Field(default=1, gt=0)
    prix_unitaire: int | None = Field(default=None, ge=0)  # négociable


class LigneCommandeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type_vetement_id: int
    type_vetement_nom: str  # nom de la prestation (rempli par le service)
    description: str | None
    quantite: int
    prix_unitaire: int
    sous_total: int


# ---------- Commandes ----------

class CommandeCreate(BaseModel):
    """Route 24. Numéro, montants et statut sont posés par le serveur."""

    client_id: int
    mesure_id: int | None = None
    lignes: list[LigneCommandeCreate] = Field(min_length=1)  # au moins une ligne
    remise: int = Field(default=0, ge=0)
    date_livraison_prevue: date | None = None  # None -> calculée (RG8)
    notes: str | None = None


class CommandeUpdate(BaseModel):
    """Route 27 : PATCH. Les lignes ont leurs propres routes (30, 31)."""

    mesure_id: int | None = None
    date_livraison_prevue: date | None = None
    remise: int | None = Field(default=None, ge=0)
    notes: str | None = None


class CommandeRead(BaseModel):
    """Détail complet (routes 24, 26, 27, 28, 30, 31)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    client_id: int
    client_nom: str
    mesure_id: int | None
    statut: StatutCommande
    date_commande: date
    date_livraison_prevue: date
    date_livraison_reelle: date | None
    remise: int
    montant_total: int
    montant_paye: int
    solde: int
    en_retard: bool
    notes: str | None
    cree_par_id: int
    created_at: datetime
    updated_at: datetime
    lignes: list[LigneCommandeRead]
    paiements: list[PaiementRead]
    livraison: LivraisonRead | None


class CommandeListe(BaseModel):
    """Élément de la liste (route 25) : client_nom, solde et en_retard inclus."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    client_id: int
    client_nom: str
    statut: StatutCommande
    date_commande: date
    date_livraison_prevue: date
    montant_total: int
    montant_paye: int
    solde: int
    en_retard: bool


# ---------- Statut et historique ----------

class StatutChange(BaseModel):
    """Route 28."""

    statut: StatutCommande
    commentaire: str | None = None


class HistoriqueStatutRead(BaseModel):
    """Route 29."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    commande_id: int
    ancien_statut: StatutCommande | None
    nouveau_statut: StatutCommande
    commentaire: str | None
    utilisateur_id: int
    date_changement: datetime