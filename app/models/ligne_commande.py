from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LigneCommande(Base):
    __tablename__ = "lignes_commande"
    __table_args__ = (
        CheckConstraint("quantite > 0", name="ck_ligne_quantite_positive"),
        CheckConstraint("prix_unitaire >= 0", name="ck_ligne_prix_positif"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # CASCADE : une ligne n'existe pas sans sa commande
    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"), index=True
    )
    type_vetement_id: Mapped[int] = mapped_column(ForeignKey("types_vetement.id"))
    description: Mapped[str | None] = mapped_column(String(255))
    quantite: Mapped[int] = mapped_column()
    prix_unitaire: Mapped[int] = mapped_column()  # FCFA, négociable (RG6)

    commande = relationship("Commande", back_populates="lignes")
    type_vetement = relationship("TypeVetement")

    # Sous-total d'une ligne, calculé (utile pour la route 26)
    @property
    def sous_total(self) -> int:
        return self.quantite * self.prix_unitaire