import base64
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, WebSocket, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from src.core.db import get_session
from src.core.settings import Settings
from src.models.receitas import ReceitaCreate, ReceitaOut, ReceitaTable, ImagemPasso
from src.models.produtos import ProdutoClienteTable
from src.service.receitas_service import criar_receita as criar_receita_db, obter_receita as obter_receita_db
from src.agents.orquestrador import Orquestrador

router = APIRouter(prefix="/receitas", tags=["receitas"])


def _executar_orquestrador(
    receita_id: int,
    produto_id: int,
    descricao_cliente: str | None,
    refs_imagens: list | None,
):
    settings = Settings()
    orquestrador = Orquestrador(settings)
    for session in get_session():
        produto = session.get(ProdutoClienteTable, produto_id)
        if produto:
            orquestrador.executar(session, receita_id, produto, descricao_cliente, refs_imagens)


@router.post("", response_model=ReceitaOut, status_code=201)
def criar_receita(
    payload: ReceitaCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    produto = session.get(ProdutoClienteTable, payload.id_produto)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    receita = criar_receita_db(session, payload)

    background_tasks.add_task(
        _executar_orquestrador,
        receita.id_receita,
        produto.id_produto,
        getattr(payload, "descricao_cliente", None),
        getattr(payload, "refs_imagens", None),
    )

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
    receita = obter_receita_db(session, receita_id)
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
async def stream_receita(
    websocket: WebSocket, receita_id: int, session: Session = Depends(get_session)
):
    await websocket.accept()
    receita = session.get(ReceitaTable, receita_id)
    if not receita:
        await websocket.send_json({"error": "Receita não encontrada"})
        await websocket.close()
        return
    await websocket.send_json({"status": receita.status, "receita_id": receita_id})
    await websocket.close()


@router.get("/{receita_id}/download", response_class=HTMLResponse)
def download_receita_html(receita_id: int, session: Session = Depends(get_session)):
    """
    Retorna o HTML da receita com imagens embutidas em base64.
    Funciona offline quando salvo como arquivo.
    """
    receita = obter_receita_db(session, receita_id)
    if not receita:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    
    if not receita.content_html:
        raise HTTPException(status_code=400, detail="Receita ainda não tem HTML gerado")
    
    html = receita.content_html
    
    # Encontrar todas as URLs de imagens no HTML
    img_pattern = r'src=["\'](/media/receitas/\d+/step_\d+\.png)["\']'
    matches = re.findall(img_pattern, html)
    
    # Substituir cada URL por base64
    for img_path in matches:
        # Remover a barra inicial para obter o caminho relativo
        file_path = Path(img_path.lstrip('/'))
        
        if file_path.exists():
            with open(file_path, 'rb') as f:
                img_data = f.read()
            b64_data = base64.b64encode(img_data).decode('utf-8')
            data_uri = f'data:image/png;base64,{b64_data}'
            html = html.replace(f'src="{img_path}"', f'src="{data_uri}"')
            html = html.replace(f"src='{img_path}'", f"src='{data_uri}'")
    
    # Criar HTML completo
    html_completo = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Receita #{receita_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
<div class="container">
{html}
</div>
</body>
</html>'''
    
    return HTMLResponse(
        content=html_completo,
        headers={
            "Content-Disposition": f"attachment; filename=receita_{receita_id}.html"
        }
    )
