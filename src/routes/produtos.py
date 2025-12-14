from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from src.core.db import get_session
from src.models.produtos import ProdutoClienteTable, ProdutoCreate, ProdutoOut

router = APIRouter(prefix="/produtos", tags=["produtos"])


@router.post("", response_model=ProdutoOut, status_code=status.HTTP_201_CREATED)
def criar_produto(payload: ProdutoCreate, session: Session = Depends(get_session)):
    produto = ProdutoClienteTable(**payload.dict())
    session.add(produto)
    session.commit()
    session.refresh(produto)
    return ProdutoOut(
        id=produto.id_produto,
        nome=produto.nome_produto,
        tipo=produto.tipo_produto,
        imagem=produto.imagem_produto,
        descricao=produto.descricao,
    )


@router.get("", response_model=list[ProdutoOut])
def listar_produtos(session: Session = Depends(get_session)):
    produtos = session.exec(select(ProdutoClienteTable)).all()
    return [
        ProdutoOut(
            id=p.id_produto,
            nome=p.nome_produto,
            tipo=p.tipo_produto,
            imagem=p.imagem_produto,
            descricao=p.descricao,
        )
        for p in produtos
    ]


@router.get("/{produto_id}", response_model=ProdutoOut)
def obter_produto(produto_id: int, session: Session = Depends(get_session)):
    produto = session.get(ProdutoClienteTable, produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return ProdutoOut(
        id=produto.id_produto,
        nome=produto.nome_produto,
        tipo=produto.tipo_produto,
        imagem=produto.imagem_produto,
        descricao=produto.descricao,
    )
