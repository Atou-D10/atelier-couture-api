from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import GenreClient


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    prenom: Mapped[str] = mapped_column(String(100))
    # Unique : le téléphone identifie le client (RG1). 21 = "+" + 20 chiffres
    telephone: Mapped[str] = mapped_column(String(21), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255))  # "| None" = facultatif
    adresse: Mapped[str | None] = mapped_column(String(255))
    genre: Mapped[GenreClient] = mapped_column(Enum(GenreClient, name="genre_client"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )