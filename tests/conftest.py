import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings

if not settings.TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL doit être défini dans le .env")

# Les migrations et l'app utiliseront la base de test (env.py lit settings.DATABASE_URL)
settings.DATABASE_URL = settings.TEST_DATABASE_URL

import app.database as database  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import RoleUtilisateur  # noqa: E402
from app.models.type_vetement import TypeVetement  # noqa: E402
from app.models.utilisateur import Utilisateur  # noqa: E402
from app.security import hash_password  # noqa: E402

engine = create_engine(settings.TEST_DATABASE_URL)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
MDP = "motdepasse1"


@pytest.fixture(scope="session", autouse=True)
def schema():
    """Construit le schéma avec Alembic (pas create_all)."""
    cfg = Config("alembic.ini")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def base_propre():
    """Vide toutes les tables avant chaque test."""
    with engine.begin() as c:
        c.execute(text(
            "TRUNCATE paiements, livraisons, historique_statuts, lignes_commande, "
            "commandes, mesures, clients, types_vetement, utilisateurs RESTART IDENTITY CASCADE"
        ))
    yield


@pytest.fixture
def db():
    with TestingSession() as session:
        yield session


@pytest.fixture
def client(db):
    def _get_db():
        yield db
    app.dependency_overrides[database.get_db] = _get_db
    # get_db est importé ailleurs sous le même objet : on surcharge l'original
    from app.database import get_db
    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _creer_user(db, email, role):
    u = Utilisateur(email=email, nom_complet=email.split("@")[0],
                    mot_de_passe_hash=hash_password(MDP), role=role, actif=True)
    db.add(u)
    db.commit()
    return u


def _headers(client, email):
    r = client.post("/api/v1/auth/login", data={"username": email, "password": MDP})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(db):
    return _creer_user(db, "admin@test.sn", RoleUtilisateur.admin)


@pytest.fixture
def admin_h(client, admin):
    return _headers(client, "admin@test.sn")


@pytest.fixture
def accueil_h(client, db):
    _creer_user(db, "accueil@test.sn", RoleUtilisateur.accueil)
    return _headers(client, "accueil@test.sn")


@pytest.fixture
def tailleur_h(client, db):
    _creer_user(db, "tailleur@test.sn", RoleUtilisateur.tailleur)
    return _headers(client, "tailleur@test.sn")


@pytest.fixture
def prestation(db):
    p = TypeVetement(nom="Boubou", prix_base=35000, delai_jours=10, actif=True)
    db.add(p)
    db.commit()
    return p