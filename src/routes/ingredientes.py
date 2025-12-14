from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session, select

from src.core.db import get_session
from src.models.ingredientes import (
    IngredienteCreate,
    IngredienteOut,
    IngredienteTable,
)

router = APIRouter(prefix="/ingredientes", tags=["ingredientes"])


@router.post("", response_model=IngredienteOut, status_code=status.HTTP_201_CREATED)
def criar_ingrediente(payload: IngredienteCreate, session: Session = Depends(get_session)):
    ingrediente = IngredienteTable(**payload.dict())
    session.add(ingrediente)
    session.commit()
    session.refresh(ingrediente)
    return IngredienteOut(
        id=ingrediente.id_ingrediente,
        nome_singular=ingrediente.nome_singular,
        nome_plural=ingrediente.nome_plural,
        tipo=ingrediente.tipo_ingrediente,
        imagem=ingrediente.imagem_ingrediente,
        descricao=ingrediente.descricao,
    )


@router.get("", response_model=list[IngredienteOut])
def listar_ingredientes(session: Session = Depends(get_session)):
    itens = session.exec(select(IngredienteTable)).all()
    return [
        IngredienteOut(
            id=i.id_ingrediente,
            nome_singular=i.nome_singular,
            nome_plural=i.nome_plural,
            tipo=i.tipo_ingrediente,
            imagem=i.imagem_ingrediente,
            descricao=i.descricao,
        )
        for i in itens
    ]


@router.get("/{ingrediente_id}", response_model=IngredienteOut)
def obter_ingrediente(ingrediente_id: int, session: Session = Depends(get_session)):
    ingrediente = session.get(IngredienteTable, ingrediente_id)
    if not ingrediente:
        raise HTTPException(status_code=404, detail="Ingrediente não encontrado")
    return IngredienteOut(
        id=ingrediente.id_ingrediente,
        nome_singular=ingrediente.nome_singular,
        nome_plural=ingrediente.nome_plural,
        tipo=ingrediente.tipo_ingrediente,
        imagem=ingrediente.imagem_ingrediente,
        descricao=ingrediente.descricao,
    )
