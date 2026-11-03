from fastapi import FastAPI

from app.exceptions import enregistrer_handlers

app = FastAPI(
    title="API Atelier de couture",
    version="1.0.0",
    docs_url="/docs",
)

enregistrer_handlers(app)


@app.get("/health")
def health():
    return {"status": "ok"}