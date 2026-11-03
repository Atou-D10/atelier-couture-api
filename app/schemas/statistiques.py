from datetime import date
from enum import Enum

from pydantic import BaseModel

from app.models.enums import StatutCommande


class Granularite(str, Enum):
    """Paramètre de la route 40."""
    jour = "jour"
    mois = "mois"


# ---------- Route 39 : tableau de bord ----------

class TableauDeBord(BaseModel):
    chiffre_affaires_mois: int
    encaisse_mois: int
    nb_commandes_mois: int
    reste_a_encaisser: int
    # Tous les statuts présents, même à 0
    commandes_par_statut: dict[StatutCommande, int]
    nb_commandes_en_retard: int
    commandes_pretes_a_livrer: int  # statut "terminee"
    livraisons_du_jour: int


# ---------- Route 40 : chiffre d'affaires par période ----------

class PointChiffreAffaires(BaseModel):
    periode: str  # "2026-11-03" (jour) ou "2026-11" (mois)
    chiffre_affaires: int
    encaisse: int


class ChiffreAffairesPeriode(BaseModel):
    granularite: Granularite
    date_debut: date
    date_fin: date
    points: list[PointChiffreAffaires]  # seulement les périodes avec activité


# ---------- Route 41 : par type de vêtement ----------

class StatTypeVetement(BaseModel):
    type_vetement_id: int
    nom: str
    quantite_vendue: int
    chiffre_affaires: int  # avant remise


# ---------- Route 42 : top clients ----------

class StatTopClient(BaseModel):
    client_id: int
    nom: str
    prenom: str
    nb_commandes: int
    chiffre_affaires: int
    solde_du: int