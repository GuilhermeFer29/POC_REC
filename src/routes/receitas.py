from fastapi import APIRouter, HTTPException, WebSocket

from src.models.receitas import ReceitaCreate, ReceitaOut

router = APIRouter(prefix="/receitas", tags=["receitas"])


@router.post("", response_model=ReceitaOut, status_code=201)
def criar_receita(payload: ReceitaCreate):
    # Será implementado na fase do orquestrador; por ora, retorno mínimo.
    return ReceitaOut(
        id=0,
        status="pending",
        json_ingredientes=None,
        json_modo_preparo=None,
        imagens=[],
        content_html=None,
        link_wp=None,
    )


@router.get("/{receita_id}", response_model=ReceitaOut)
def obter_receita(receita_id: int):
    raise HTTPException(status_code=404, detail="Receita não encontrada")


@router.websocket("/stream/{receita_id}")
async def stream_receita(websocket: WebSocket, receita_id: int):
    await websocket.accept()
    await websocket.send_json({"status": "pending", "receita_id": receita_id})
    await websocket.close()
