from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import StatutCommande


class HistoriqueStatut(Base):
    __tablename__ = "historique_statuts"

    id: Mapped[int] = mapped_column(primary_key=True)
    commande_id: Mapped[int] = mapped_column(ForeignKey("commandes.id"), index=True)
    # name= identique : on réutilise le même type enum PostgreSQL que Commande
    # None à la création de la commande (RG15)
    ancien_statut: Mapped[StatutCommande | None] = mapped_column(
        Enum(StatutCommande, name="statut_commande")
    )
    nouveau_statut: Mapped[StatutCommande] = mapped_column(
        Enum(StatutCommande, name="statut_commande")
    )
    commentaire: Mapped[str | None] = mapped_column(Text)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    date_changement: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    commande = relationship("Commande", back_populates="historique")