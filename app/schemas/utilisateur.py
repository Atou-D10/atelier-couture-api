from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import RoleUtilisateur


class UtilisateurCreate(BaseModel):
    """Création d'un compte (route 3). Le mot de passe arrive en clair, il sera haché par le service."""

    email: EmailStr
    nom_complet: str = Field(min_length=1, max_length=150)
    mot_de_passe: str = Field(min_length=8, max_length=128)  # RG21 : 8 caractères minimum
    role: RoleUtilisateur


class UtilisateurUpdate(BaseModel):
    """Modification partielle (route 6) : tous les champs sont facultatifs."""

    nom_complet: str | None = Field(default=None, min_length=1, max_length=150)
    role: RoleUtilisateur | None = None
    actif: bool | None = None
    mot_de_passe: str | None = Field(default=None, min_length=8, max_length=128)


class UtilisateurRead(BaseModel):
    """Ce que l'API renvoie : AUCUN champ mot_de_passe / mot_de_passe_hash."""

    model_config = ConfigDict(from_attributes=True)  # permet de lire un objet SQLAlchemy

    id: int
    email: EmailStr
    nom_complet: str
    role: RoleUtilisateur
    actif: bool
    created_at: datetime