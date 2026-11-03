from fastapi import FastAPI

app = FastAPI(
    title="API Atelier de couture",
    version="1.0.0",
    docs_url="/docs",
)


@app.get("/health")
def health():
    return {"status": "ok"}