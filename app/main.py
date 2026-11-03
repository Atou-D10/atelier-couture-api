from fastapi import APIRouter, FastAPI

from app.exceptions import enregistrer_handlers
from app.routers import auth, utilisateurs

app = FastAPI(
    title="API Atelier de couture",
    version="1.0.0",
    docs_url="/docs",
)

enregistrer_handlers(app)

# Toutes les routes métier sont sous /api/v1 (sauf /health)
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth.router)
api_v1.include_router(utilisateurs.router)
app.include_router(api_v1)

@app.get("/health")
def health():
    return {"status": "ok"}