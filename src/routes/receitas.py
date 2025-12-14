from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlmodel import Session, select

from src.core.db import get_session
from src.models.receitas import ReceitaCreate, ReceitaOut, ReceitaTable, ImagemPasso

router = APIRouter(prefix="/receitas", tags=["receitas"])


@router.post("", response_model=ReceitaOut, status_code=201)
def criar_receita(payload: ReceitaCreate, session: Session = Depends(get_session)):
    receita = ReceitaTable(
        id_produto=payload.id_produto,
        status="pending",
        json_ingredientes=None,
        json_modo_preparo=None,
        content_html=None,
        link_wp=None,
    )
    session.add(receita)
    session.commit()
    session.refresh(receita)
    return ReceitaOut(
        id=receita.id_receita,
        status=receita.status,
        json_ingredientes=None,
        json_modo_preparo=None,
        imagens=[],
        content_html=None,
        link_wp=None,
    )


@router.get("/{receita_id}", response_model=ReceitaOut)
def obter_receita(receita_id: int, session: Session = Depends(get_session)):
    receita = session.get(ReceitaTable, receita_id)
    if not receita:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    imagens: list[ImagemPasso] = []
    return ReceitaOut(
        id=receita.id_receita,
        status=receita.status,
        json_ingredientes=receita.json_ingredientes,
        json_modo_preparo=receita.json_modo_preparo,
        imagens=imagens,
        content_html=receita.content_html,
        link_wp=receita.link_wp,
    )


@router.websocket("/stream/{receita_id}")
async def stream_receita(websocket: WebSocket, receita_id: int):
    await websocket.accept()
    await websocket.send_json({"status": "pending", "receita_id": receita_id})
    await websocket.close()
