from pydantic import BaseModel, ConfigDict, Field


class TypeVetementCreate(BaseModel):
    """Route 14 : ajout d'une prestation (nom unique vérifié par le service, 409)."""

    nom: str = Field(min_length=1, max_length=100)
    description: str | None = None
    prix_base: int = Field(ge=0)    # FCFA, entier
    delai_jours: int = Field(ge=0)  # en jours


class TypeVetementUpdate(BaseModel):
    """Route 17 : PATCH, tous les champs facultatifs.
    actif=false retire la prestation sans toucher aux anciennes commandes."""

    nom: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    prix_base: int | None = Field(default=None, ge=0)
    delai_jours: int | None = Field(default=None, ge=0)
    actif: bool | None = None


class TypeVetementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    description: str | None
    prix_base: int
    delai_jours: int
    actif: bool