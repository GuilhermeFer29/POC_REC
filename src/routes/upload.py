import os
import shutil
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlmodel import Session

from src.core.db import get_session
from src.core.settings import Settings
from src.models.produtos import ProdutoClienteTable
from src.service.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

MEDIA_DIR = Path("media")
PRODUTOS_DIR = MEDIA_DIR / "produtos"
RECEITAS_DIR = MEDIA_DIR / "receitas"
RAG_DIR = MEDIA_DIR / "rag"

PRODUTOS_DIR.mkdir(parents=True, exist_ok=True)
RECEITAS_DIR.mkdir(parents=True, exist_ok=True)
RAG_DIR.mkdir(parents=True, exist_ok=True)


class UploadResponse(BaseModel):
    filename: str
    path: str
    message: str


@router.post("/produto/{produto_id}", response_model=UploadResponse)
async def upload_imagem_produto(
    produto_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    produto_dir = PRODUTOS_DIR / str(produto_id)
    produto_dir.mkdir(parents=True, exist_ok=True)

    file_ext = Path(file.filename).suffix or ".png"
    filename = f"produto_{produto_id}{file_ext}"
    file_path = produto_dir / filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Atualizar o caminho da imagem no banco de dados
    produto = session.get(ProdutoClienteTable, produto_id)
    if produto:
        produto.imagem_produto = str(file_path)
        session.add(produto)
        session.commit()

    return UploadResponse(
        filename=filename,
        path=str(file_path),
        message=f"Imagem do produto {produto_id} salva com sucesso",
    )


@router.post("/receita/{receita_id}/step/{step_index}", response_model=UploadResponse)
async def upload_imagem_passo(
    receita_id: int,
    step_index: int,
    file: UploadFile = File(...),
):
    receita_dir = RECEITAS_DIR / str(receita_id)
    receita_dir.mkdir(parents=True, exist_ok=True)

    file_ext = Path(file.filename).suffix or ".png"
    filename = f"step_{step_index}{file_ext}"
    file_path = receita_dir / filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return UploadResponse(
        filename=filename,
        path=str(file_path),
        message=f"Imagem do passo {step_index} da receita {receita_id} salva",
    )


def _process_pdf_background(file_path: str, tipo: str):
    """Processa PDF em background e adiciona ao RAG."""
    try:
        settings = Settings()
        rag_service = RAGService(settings)
        result = rag_service.process_pdf_file(file_path, tipo)
        logger.info(f"PDF processado em background: {result}")
    except Exception as e:
        logger.error(f"Erro ao processar PDF em background: {e}")


@router.post("/rag/{tipo}", response_model=UploadResponse)
async def upload_arquivo_rag(
    tipo: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    if tipo not in ["receitas", "fotografia"]:
        raise HTTPException(status_code=400, detail="Tipo deve ser 'receitas' ou 'fotografia'")

    tipo_dir = RAG_DIR / tipo
    tipo_dir.mkdir(parents=True, exist_ok=True)

    filename = file.filename or "arquivo"
    file_path = tipo_dir / filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Se for PDF, processar automaticamente em background
    if filename.lower().endswith('.pdf'):
        logger.info(f"Iniciando processamento do PDF {filename} para RAG {tipo}")
        background_tasks.add_task(_process_pdf_background, str(file_path), tipo)
        message = f"Arquivo '{filename}' salvo e processamento iniciado para RAG {tipo}"
    else:
        message = f"Arquivo '{filename}' salvo para RAG {tipo}"

    return UploadResponse(
        filename=filename,
        path=str(file_path),
        message=message,
    )


@router.post("/rag/{tipo}/processar")
async def processar_pdfs_rag(
    tipo: str,
    background_tasks: BackgroundTasks,
):
    """Processa todos os PDFs existentes na pasta RAG do tipo especificado."""
    if tipo not in ["receitas", "fotografia"]:
        raise HTTPException(status_code=400, detail="Tipo deve ser 'receitas' ou 'fotografia'")

    tipo_dir = RAG_DIR / tipo
    if not tipo_dir.exists():
        raise HTTPException(status_code=404, detail=f"Pasta RAG/{tipo} não existe")

    pdfs = list(tipo_dir.glob("*.pdf")) + list(tipo_dir.glob("*.PDF"))
    
    if not pdfs:
        return {"message": f"Nenhum PDF encontrado em RAG/{tipo}", "count": 0}

    for pdf_path in pdfs:
        logger.info(f"Agendando processamento: {pdf_path.name}")
        background_tasks.add_task(_process_pdf_background, str(pdf_path), tipo)

    return {
        "message": f"Processamento iniciado para {len(pdfs)} PDFs em RAG/{tipo}",
        "count": len(pdfs),
        "files": [p.name for p in pdfs],
    }


@router.get("/listar/{tipo}")
def listar_arquivos(tipo: str):
    if tipo == "produtos":
        base_dir = PRODUTOS_DIR
    elif tipo == "receitas":
        base_dir = RECEITAS_DIR
    elif tipo == "rag":
        base_dir = RAG_DIR
    else:
        raise HTTPException(status_code=400, detail="Tipo inválido")

    arquivos = []
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            full_path = Path(root) / f
            arquivos.append({
                "nome": f,
                "caminho": str(full_path),
                "tamanho": full_path.stat().st_size,
            })

    return {"tipo": tipo, "arquivos": arquivos}
