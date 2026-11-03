from datetime import date, datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ModePaiement


class Paiement(Base):
    __tablename__ = "paiements"
    # Garde-fou en base : un paiement est strictement positif (RG16)
    __table_args__ = (
        CheckConstraint("montant > 0", name="ck_paiement_montant_positif"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    commande_id: Mapped[int] = mapped_column(ForeignKey("commandes.id"), index=True)
    montant: Mapped[int] = mapped_column()  # FCFA, entier
    mode: Mapped[ModePaiement] = mapped_column(Enum(ModePaiement, name="mode_paiement"))
    reference: Mapped[str | None] = mapped_column(String(100))  # ex. n° de transaction Wave
    date_paiement: Mapped[date] = mapped_column(default=date.today)
    enregistre_par_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    commande = relationship("Commande", back_populates="paiements")