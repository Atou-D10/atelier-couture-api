# API Atelier de couture

API REST (FastAPI, SQLAlchemy 2, PostgreSQL, Alembic) de gestion d'un atelier de couture :
clients, mesures, commandes, paiements, livraisons, statistiques.

## Prérequis
- Python 3.12
- Docker Desktop (pour le lancement conteneurisé)
- PostgreSQL (uniquement pour le lancement local sans Docker)

## Configuration
```bash
cp .env.example .env      # Windows : Copy-Item .env.example .env
```
Éditez `.env` : `SECRET_KEY` (générez-la avec
`python -c "import secrets; print(secrets.token_hex(32))"`), `ADMIN_PASSWORD`,
mots de passe PostgreSQL et comptes de démonstration. Ne commitez jamais `.env`.

## Lancement avec Docker (recommandé)
```bash
docker compose up --build
```
Au démarrage : migrations (`alembic upgrade head`), seed (`python -m app.seed`),
puis API sur http://localhost:8000 (Swagger : http://localhost:8000/docs).
Arrêt : `docker compose down` (`-v` pour supprimer aussi les données).

## Lancement en local
```bash
python3.12 -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\Activate.ps1
pip install -r requirements.txt
# DATABASE_URL du .env doit pointer vers votre PostgreSQL local
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

## Tests
Créez une base dédiée (ex. `atelier_test`) et renseignez `TEST_DATABASE_URL` dans `.env`.
Le schéma de test est construit par `alembic upgrade head`.
```bash
pytest -v
```

## Comptes de test (créés par le seed)
| Rôle | E-mail | Mot de passe |
|---|---|---|
| admin | valeur de `ADMIN_EMAIL` | `ADMIN_PASSWORD` |
| accueil | `DEMO_ACCUEIL_EMAIL` | `DEMO_ACCUEIL_PASSWORD` |
| tailleur | `DEMO_TAILLEUR_EMAIL` | `DEMO_TAILLEUR_PASSWORD` |

Connexion : `POST /api/v1/auth/login` (formulaire `username` = e-mail, `password`),
puis en-tête `Authorization: Bearer <access_token>`.

## Routes réalisées (préfixe `/api/v1`, sauf `/health`)
| N° | Méthode | Chemin | Rôle |
|---|---|---|---|
| 1 | POST | /auth/login | Public |
| 2 | GET | /auth/me | Connecté |
| 3 | POST | /utilisateurs | Admin |
| 4 | GET | /utilisateurs | Admin |
| 5 | GET | /utilisateurs/{id} | Admin |
| 6 | PATCH | /utilisateurs/{id} | Admin |
| 7 | POST | /clients | Tous |
| 8 | GET | /clients | Tous |
| 9 | GET | /clients/{id} | Tous |
| 10 | PATCH | /clients/{id} | Tous |
| 11 | DELETE | /clients/{id} | Admin |
| 12 | GET | /clients/{id}/commandes | Tous |
| 13 | GET | /clients/{id}/resume | Tous |
| 14 | POST | /catalogue | Admin |
| 15 | GET | /catalogue | Tous |
| 16 | GET | /catalogue/{id} | Tous |
| 17 | PATCH | /catalogue/{id} | Admin |
| 18 | POST | /clients/{id}/mesures | Tailleur |
| 19 | GET | /clients/{id}/mesures | Tous |
| 20 | GET | /clients/{id}/mesures/derniere | Tous |
| 21 | GET | /mesures/{id} | Tous |
| 22 | PATCH | /mesures/{id} | Tailleur |
| 23 | DELETE | /mesures/{id} | Tailleur |
| 24 | POST | /commandes | Accueil |
| 25 | GET | /commandes | Tous |
| 26 | GET | /commandes/{id} | Tous |
| 27 | PATCH | /commandes/{id} | Accueil |
| 28 | POST | /commandes/{id}/statut | Tous (RG13-14) |
| 29 | GET | /commandes/{id}/historique | Tous |
| 30 | POST | /commandes/{id}/lignes | Accueil |
| 31 | DELETE | /commandes/{id}/lignes/{ligne_id} | Accueil |
| 32 | POST | /commandes/{id}/paiements | Accueil |
| 33 | GET | /commandes/{id}/paiements | Tous |
| 34 | DELETE | /paiements/{id} | Admin |
| 35 | PUT | /commandes/{id}/livraison | Accueil |
| 36 | GET | /commandes/{id}/livraison | Tous |
| 37 | POST | /commandes/{id}/livraison/confirmer | Accueil |
| 38 | GET | /livraisons | Tous |
| 39 | GET | /statistiques/tableau-de-bord | Admin |
| 40 | GET | /statistiques/chiffre-affaires | Admin |
| 41 | GET | /statistiques/types-vetement | Admin |
| 42 | GET | /statistiques/top-clients | Admin |
| 43 | GET | /statistiques/impayes | Admin |
| 44 | GET | /health (sans préfixe) | Public |

L'admin est autorisé sur toutes les routes.

## Architecture
`app/routers` (droits, appel du service, commit) · `app/services` (règles de gestion) ·
`app/models` (SQLAlchemy) · `app/schemas` (Pydantic) · `alembic/` (migrations) · `tests/`.
