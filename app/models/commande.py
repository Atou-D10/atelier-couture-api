from datetime import date, datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import StatutCommande


class Commande(Base):
    __tablename__ = "commandes"
    # Garde-fous en base (la validation principale reste dans les services)
    __table_args__ = (
        CheckConstraint("remise >= 0", name="ck_commande_remise_positive"),
        CheckConstraint("montant_total >= 0", name="ck_commande_total_positif"),
        CheckConstraint("montant_paye >= 0", name="ck_commande_paye_positif"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Format CMD-AAAA-NNNNN (RG5), généré par le service
    numero: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    # Pas de ondelete=CASCADE : un client avec commandes ne se supprime pas (RG4)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    # Facultatif, et pas de cascade non plus (RG4)
    mesure_id: Mapped[int | None] = mapped_column(ForeignKey("mesures.id"))
    statut: Mapped[StatutCommande] = mapped_column(
        Enum(StatutCommande, name="statut_commande"),
        default=StatutCommande.en_attente,
        server_default=StatutCommande.en_attente.value,
        index=True,
    )
    date_commande: Mapped[date] = mapped_column(default=date.today)
    date_livraison_prevue: Mapped[date] = mapped_column(index=True)
    date_livraison_reelle: Mapped[date | None] = mapped_column()
    remise: Mapped[int] = mapped_column(default=0, server_default="0")
    montant_total: Mapped[int] = mapped_column(default=0, server_default="0")
    montant_paye: Mapped[int] = mapped_column(default=0, server_default="0")
    notes: Mapped[str | None] = mapped_column(Text)
    cree_par_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relations : accès direct aux objets liés (commande.lignes, commande.client...)
    client = relationship("Client", back_populates="commandes")
    mesure = relationship("Mesure")
    lignes = relationship(
        "LigneCommande",
        back_populates="commande",
        cascade="all, delete-orphan",  # retirer une ligne de la liste la supprime
        order_by="LigneCommande.id",
    )
    historique = relationship(
        "HistoriqueStatut",
        back_populates="commande",
        order_by="HistoriqueStatut.id",
    )
    paiements = relationship(
        "Paiement",
        back_populates="commande",
        order_by="Paiement.id",  # ordre de saisie (route 33)
    )
    # uselist=False : 0 ou 1 livraison, donc un objet et non une liste
    livraison = relationship(
        "Livraison", back_populates="commande", uselist=False
    )

    # Le solde n'est pas stocké : il se calcule (RG7)
    @property
    def solde(self) -> int:
        return self.montant_total - self.montant_paye