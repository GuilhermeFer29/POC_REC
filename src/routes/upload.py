import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel

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
):
    produto_dir = PRODUTOS_DIR / str(produto_id)
    produto_dir.mkdir(parents=True, exist_ok=True)

    file_ext = Path(file.filename).suffix or ".png"
    filename = f"produto_{produto_id}{file_ext}"
    file_path = produto_dir / filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

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


@router.post("/rag/{tipo}", response_model=UploadResponse)
async def upload_arquivo_rag(
    tipo: str,
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

    return UploadResponse(
        filename=filename,
        path=str(file_path),
        message=f"Arquivo '{filename}' salvo para RAG {tipo}",
    )


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
