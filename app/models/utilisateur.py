from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import RoleUtilisateur


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nom_complet: Mapped[str] = mapped_column(String(150))
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255))  # jamais en clair
    role: Mapped[RoleUtilisateur] = mapped_column(Enum(RoleUtilisateur, name="role_utilisateur"))
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )