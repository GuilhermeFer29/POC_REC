from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional

from src.core.settings import Settings
from src.service.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])

settings = Settings()
rag_service = RAGService(settings)


class ContentInput(BaseModel):
    name: str
    content: str
    metadata: Optional[dict] = None


class UrlInput(BaseModel):
    name: str
    url: HttpUrl
    metadata: Optional[dict] = None


class SearchInput(BaseModel):
    query: str
    num_documents: int = 5


class SearchResult(BaseModel):
    results: list


@router.post("/receitas/content")
def add_receita_content(payload: ContentInput):
    rag_service.add_receita_content(
        name=payload.name,
        content=payload.content,
        metadata=payload.metadata,
    )
    return {"status": "ok", "message": f"Conteúdo '{payload.name}' adicionado à base de receitas"}


@router.post("/receitas/url")
def add_receita_from_url(payload: UrlInput):
    rag_service.add_receita_from_url(
        name=payload.name,
        url=str(payload.url),
        metadata=payload.metadata,
    )
    return {"status": "ok", "message": f"URL '{payload.name}' adicionada à base de receitas"}


@router.post("/receitas/search", response_model=SearchResult)
def search_receitas(payload: SearchInput):
    results = rag_service.search_receitas(
        query=payload.query,
        num_documents=payload.num_documents,
    )
    return SearchResult(results=results or [])


@router.post("/fotografia/content")
def add_fotografia_content(payload: ContentInput):
    rag_service.add_fotografia_content(
        name=payload.name,
        content=payload.content,
        metadata=payload.metadata,
    )
    return {"status": "ok", "message": f"Conteúdo '{payload.name}' adicionado à base de fotografia"}


@router.post("/fotografia/url")
def add_fotografia_from_url(payload: UrlInput):
    rag_service.add_fotografia_from_url(
        name=payload.name,
        url=str(payload.url),
        metadata=payload.metadata,
    )
    return {"status": "ok", "message": f"URL '{payload.name}' adicionada à base de fotografia"}


@router.post("/fotografia/search", response_model=SearchResult)
def search_fotografia(payload: SearchInput):
    results = rag_service.search_fotografia(
        query=payload.query,
        num_documents=payload.num_documents,
    )
    return SearchResult(results=results or [])
