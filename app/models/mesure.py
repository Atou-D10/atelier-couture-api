from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# Les 18 mesures de l'énoncé (en cm), dans l'ordre
CHAMPS_MESURES = [
    "taille_cm", "tour_cou", "carrure_dos", "longueur_epaule",
    "tour_poitrine", "tour_taille", "tour_bassin", "longueur_manche",
    "tour_bras", "tour_poignet", "longueur_dos", "longueur_haut",
    "longueur_pantalon", "tour_cuisse", "tour_genou", "bas_pantalon",
    "entrejambe", "longueur_robe",
]


class Mesure(Base):
    __tablename__ = "mesures"
    # RG2 en base : chaque mesure est NULL ou comprise entre 0 (exclu) et 300 cm
    __table_args__ = tuple(
        CheckConstraint(
            f"{c} IS NULL OR ({c} > 0 AND {c} <= 300)", name=f"ck_mesure_{c}"
        )
        for c in CHAMPS_MESURES
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # CASCADE : supprimer un client supprime ses mesures (route 11)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    date_prise: Mapped[date] = mapped_column(Date, default=date.today)
    prise_par_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    notes: Mapped[str | None] = mapped_column(Text)

    # Les 18 mesures, toutes facultatives (nullable)
    taille_cm: Mapped[float | None] = mapped_column(Numeric(5, 1))
    tour_cou: Mapped[float | None] = mapped_column(Numeric(5, 1))
    carrure_dos: Mapped[float | None] = mapped_column(Numeric(5, 1))
    longueur_epaule: Mapped[float | None] = mapped_column(Numeric(5, 1))
    tour_poitrine: Mapped[float | None] = mapped_column(Numeric(5, 1))
    tour_taille: Mapped[float | None] = mapped_column(Numeric(5, 1))
    tour_bassin: Mapped[float | None] = mapped_column(Numeric(5, 1))
    longueur_manche: Mapped[float | None] = mapped_column(Numeric(5, 1))
    tour_bras: Mapped[float | None] = mapped_column(Numeric(5, 1))
    tour_poignet: Mapped[float | None] = mapped_column(Numeric(5, 1))
    longueur_dos: Mapped[float | None] = mapped_column(Numeric(5, 1))
    longueur_haut: Mapped[float | None] = mapped_column(Numeric(5, 1))
    longueur_pantalon: Mapped[float | None] = mapped_column(Numeric(5, 1))
    tour_cuisse: Mapped[float | None] = mapped_column(Numeric(5, 1))
    tour_genou: Mapped[float | None] = mapped_column(Numeric(5, 1))
    bas_pantalon: Mapped[float | None] = mapped_column(Numeric(5, 1))
    entrejambe: Mapped[float | None] = mapped_column(Numeric(5, 1))
    longueur_robe: Mapped[float | None] = mapped_column(Numeric(5, 1))