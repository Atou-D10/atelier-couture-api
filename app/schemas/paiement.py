from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ModePaiement


class PaiementCreate(BaseModel):
    """Route 32. Les règles (<= solde, date non future) sont dans le service (RG16)."""

    montant: int = Field(gt=0)
    mode: ModePaiement
    reference: str | None = Field(default=None, max_length=100)
    date_paiement: date | None = None  # None -> aujourd'hui


class PaiementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commande_id: int
    montant: int
    mode: ModePaiement
    reference: str | None
    date_paiement: date
    enregistre_par_id: int
    created_at: datetime