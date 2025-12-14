from fastapi import APIRouter, HTTPException

from src.models.produtos import ProdutoOut

router = APIRouter(prefix="/produtos", tags=["produtos"])


@router.get("", response_model=list[ProdutoOut])
def listar_produtos():
    return []


@router.get("/{produto_id}", response_model=ProdutoOut)
def obter_produto(produto_id: int):
    raise HTTPException(status_code=404, detail="Produto não encontrado")
