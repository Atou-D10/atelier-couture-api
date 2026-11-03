from datetime import date

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ModeLivraison, StatutLivraison


class Livraison(Base):
    __tablename__ = "livraisons"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique=True : une seule livraison par commande (RG18)
    commande_id: Mapped[int] = mapped_column(ForeignKey("commandes.id"), unique=True)
    mode: Mapped[ModeLivraison] = mapped_column(Enum(ModeLivraison, name="mode_livraison"))
    adresse: Mapped[str | None] = mapped_column(String(255))  # obligatoire si domicile (service)
    livreur: Mapped[str | None] = mapped_column(String(100))
    date_prevue: Mapped[date] = mapped_column()
    date_effective: Mapped[date | None] = mapped_column()
    statut: Mapped[StatutLivraison] = mapped_column(
        Enum(StatutLivraison, name="statut_livraison"),
        default=StatutLivraison.planifiee,
        server_default=StatutLivraison.planifiee.value,
    )
    notes: Mapped[str | None] = mapped_column(Text)

    commande = relationship("Commande", back_populates="livraison")