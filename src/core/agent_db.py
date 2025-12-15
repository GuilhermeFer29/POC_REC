"""
Database compartilhado para persistência de sessão entre agentes.
Permite que Chef, Fotógrafo e Diagramador compartilhem contexto.
"""
from agno.db.sqlite import SqliteDb
from pathlib import Path


def get_agent_db() -> SqliteDb:
    """
    Retorna uma instância do banco de dados SQLite para os agentes.
    Todos os agentes compartilham o mesmo banco para manter contexto.
    """
    db_path = Path("data/agents.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    return SqliteDb(
        db_file=str(db_path),
    )
