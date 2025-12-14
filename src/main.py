from fastapi import FastAPI, Request
from uuid import uuid4

from .core.settings import Settings
from .core.db import init_engine, create_db_and_tables
from .core.qdrant_client import get_qdrant_client
from .routes.produtos import router as produtos_router
from .routes.ingredientes import router as ingredientes_router
from .routes.receitas import router as receitas_router


settings = Settings()
engine = init_engine(settings)
qdrant_client = get_qdrant_client(settings)

app = FastAPI(title="POC Receitas", version="0.1.0")

app.include_router(produtos_router)
app.include_router(ingredientes_router)
app.include_router(receitas_router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.get("/health")
def health():
    return {
        "status": "ok",
        "db_url": settings.mysql_url,
        "qdrant_host": settings.qdrant_host,
    }
