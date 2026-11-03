from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.mesure import CHAMPS_MESURES

# Une mesure : strictement positive (> 0) et <= 300 cm (RG2)
Cm = Field(default=None, gt=0, le=300)


class _MesuresBase(BaseModel):
    """Les 18 mesures facultatives (en cm)."""

    taille_cm: float | None = Cm
    tour_cou: float | None = Cm
    carrure_dos: float | None = Cm
    longueur_epaule: float | None = Cm
    tour_poitrine: float | None = Cm
    tour_taille: float | None = Cm
    tour_bassin: float | None = Cm
    longueur_manche: float | None = Cm
    tour_bras: float | None = Cm
    tour_poignet: float | None = Cm
    longueur_dos: float | None = Cm
    longueur_haut: float | None = Cm
    longueur_pantalon: float | None = Cm
    tour_cuisse: float | None = Cm
    tour_genou: float | None = Cm
    bas_pantalon: float | None = Cm
    entrejambe: float | None = Cm
    longueur_robe: float | None = Cm


class MesureCreate(_MesuresBase):
    """Route 18. client_id vient de l'URL, prise_par_id du jeton."""

    date_prise: date | None = None  # None -> aujourd'hui (défini par le service)
    notes: str | None = None

    @model_validator(mode="after")
    def _au_moins_une(self):
        # RG2 : une prise doit contenir au moins une mesure
        if all(getattr(self, c) is None for c in CHAMPS_MESURES):
            raise ValueError("Une prise de mesures doit contenir au moins une mesure.")
        return self


class MesureUpdate(_MesuresBase):
    """Route 22 : PATCH. Le contrôle « il reste au moins une mesure »
    se fait dans le service, après fusion avec les valeurs existantes."""

    date_prise: date | None = None
    notes: str | None = None


class MesureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    date_prise: date
    prise_par_id: int
    notes: str | None
    taille_cm: float | None
    tour_cou: float | None
    carrure_dos: float | None
    longueur_epaule: float | None
    tour_poitrine: float | None
    tour_taille: float | None
    tour_bassin: float | None
    longueur_manche: float | None
    tour_bras: float | None
    tour_poignet: float | None
    longueur_dos: float | None
    longueur_haut: float | None
    longueur_pantalon: float | None
    tour_cuisse: float | None
    tour_genou: float | None
    bas_pantalon: float | None
    entrejambe: float | None
    longueur_robe: float | None