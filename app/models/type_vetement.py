from sqlalchemy import Boolean, CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TypeVetement(Base):
    __tablename__ = "types_vetement"
    # Garde-fous au niveau de la base : pas de prix ni délai négatifs
    __table_args__ = (
        CheckConstraint("prix_base >= 0", name="ck_type_prix_positif"),
        CheckConstraint("delai_jours >= 0", name="ck_type_delai_positif"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    prix_base: Mapped[int] = mapped_column()    # FCFA, entier
    delai_jours: Mapped[int] = mapped_column()
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")