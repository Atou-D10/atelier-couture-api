from fastapi import APIRouter, FastAPI

from app.exceptions import enregistrer_handlers
from app.routers import (
    auth, catalogue, clients, commandes, livraisons, mesures, paiements, utilisateurs,
)
app = FastAPI(
    title="API Atelier de couture",
    version="1.0.0",
    docs_url="/docs",
)

enregistrer_handlers(app)

# Toutes les routes métier sont sous /api/v1 (sauf /health)
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth.router)
api_v1.include_router(clients.router)
api_v1.include_router(mesures.router_client)
api_v1.include_router(commandes.router)
api_v1.include_router(mesures.router)
api_v1.include_router(utilisateurs.router)
api_v1.include_router(paiements.router_commande)
api_v1.include_router(paiements.router)
api_v1.include_router(livraisons.router_commande)
api_v1.include_router(livraisons.router)
api_v1.include_router(catalogue.router)
app.include_router(api_v1)

@app.get("/health")
def health():
    return {"status": "ok"}