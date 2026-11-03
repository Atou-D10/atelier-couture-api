from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings  # nos variables du .env (DATABASE_URL...)

# L'engine = la "connexion" à PostgreSQL, créée une seule fois.
# Il gère un pool de connexions réutilisables.
# pool_pre_ping=True : avant de réutiliser une connexion, on vérifie
# qu'elle est encore vivante (évite les erreurs si la base a redémarré).
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# SessionLocal = une "usine" à sessions.
# Une session = une conversation avec la base (lire, ajouter, modifier).
# autoflush=False : SQLAlchemy n'envoie pas les changements à la base
#   automatiquement avant chaque requête, on garde le contrôle.
# expire_on_commit=False : après un commit, les objets gardent leurs
#   valeurs en mémoire (sinon SQLAlchemy les recharge à chaque accès).
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# Classe de base dont hériteront TOUS nos modèles (Client, Commande...).
# Elle garde la liste de toutes les tables : Alembic s'en sert plus tard
# (Base.metadata) pour générer les migrations.
class Base(DeclarativeBase):
    pass


# Dépendance FastAPI : sera utilisée dans les routes avec Depends(get_db).
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()   # on ouvre une session pour cette requête
    try:
        yield db          # on la "prête" à la route
    finally:
        db.close()        # quoi qu'il arrive, on la ferme à la fin