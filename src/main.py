from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from uuid import uuid4
from pathlib import Path

from .core.settings import Settings
from .core.db import init_engine, create_db_and_tables
from .core.qdrant_client import get_qdrant_client
from .routes.produtos import router as produtos_router
from .routes.ingredientes import router as ingredientes_router
from .routes.receitas import router as receitas_router
from .routes.rag import router as rag_router
from .routes.upload import router as upload_router
from .routes.ingredientes_api import router as ingredientes_api_router
from .routes.themealdb import router as themealdb_router
from .routes.enriquecimento import router as enriquecimento_router


settings = Settings()
engine = init_engine(settings)
qdrant_client = get_qdrant_client(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="POC Receitas", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

app.include_router(produtos_router)
app.include_router(ingredientes_router)
app.include_router(receitas_router)
app.include_router(rag_router)
app.include_router(upload_router)
app.include_router(ingredientes_api_router)
app.include_router(themealdb_router)
app.include_router(enriquecimento_router)

media_path = Path("media")
media_path.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_path)), name="media")


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
