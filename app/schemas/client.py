import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import GenreClient


def normaliser_telephone(valeur: str) -> str:
    """RG1 : supprime espaces, points, tirets, parenthèses, puis valide.
    Forme valide : 6 à 20 chiffres, avec un '+' initial facultatif."""
    nettoye = re.sub(r"[\s.\-()]", "", valeur)
    if not re.fullmatch(r"\+?\d{6,20}", nettoye):
        raise ValueError(
            "Téléphone invalide : 6 à 20 chiffres, avec un '+' initial facultatif."
        )
    return nettoye


class ClientCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    telephone: str
    email: EmailStr | None = None
    adresse: str | None = Field(default=None, max_length=255)
    genre: GenreClient
    notes: str | None = None

    @field_validator("telephone")
    @classmethod
    def _tel(cls, v: str) -> str:
        return normaliser_telephone(v)


class ClientUpdate(BaseModel):
    """PATCH (route 10) : tout est facultatif, mais nom, prenom et telephone
    ne peuvent pas être vidés (422) : on refuse None et la chaîne vide."""

    nom: str | None = Field(default=None, min_length=1, max_length=100)
    prenom: str | None = Field(default=None, min_length=1, max_length=100)
    telephone: str | None = None
    email: EmailStr | None = None
    adresse: str | None = Field(default=None, max_length=255)
    genre: GenreClient | None = None
    notes: str | None = None

    @field_validator("telephone")
    @classmethod
    def _tel(cls, v: str | None) -> str | None:
        return None if v is None else normaliser_telephone(v)

    @field_validator("nom", "prenom", "telephone", mode="before")
    @classmethod
    def _non_vidable(cls, v, info):
        # Si le champ est envoyé explicitement à null, on refuse.
        # (Un champ non envoyé n'appelle pas ce validateur.)
        if v is None:
            raise ValueError(f"Le champ '{info.field_name}' ne peut pas être vidé.")
        return v


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    prenom: str
    telephone: str
    email: EmailStr | None
    adresse: str | None
    genre: GenreClient
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ClientResume(BaseModel):
    """Route 13 : /clients/{id}/resume (commandes annulées exclues)."""

    nb_commandes: int
    chiffre_affaires: int
    total_paye: int
    solde_du: int
    derniere_commande: datetime | None  # date de la commande la plus récente
    a_des_mesures: bool