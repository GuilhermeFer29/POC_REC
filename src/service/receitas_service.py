from typing import Optional

from sqlmodel import Session

from src.models.receitas import ReceitaCreate, ReceitaTable


def criar_receita(session: Session, payload: ReceitaCreate) -> ReceitaTable:
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
    return receita


def obter_receita(session: Session, receita_id: int) -> Optional[ReceitaTable]:
    return session.get(ReceitaTable, receita_id)


def atualizar_status(
    session: Session, receita_id: int, novo_status: str
) -> Optional[ReceitaTable]:
    receita = session.get(ReceitaTable, receita_id)
    if not receita:
        return None
    receita.status = novo_status
    session.add(receita)
    session.commit()
    session.refresh(receita)
    return receita
