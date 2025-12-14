from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from .settings import Settings

_engine = None


def init_engine(settings: Settings):
    global _engine
    if _engine is None:
        _engine = create_engine(settings.mysql_url, echo=False)
    return _engine


def get_session() -> Generator[Session, None, None]:
    if _engine is None:
        raise RuntimeError("Database engine not initialized.")
    with Session(_engine) as session:
        yield session


def create_db_and_tables():
    if _engine is None:
        raise RuntimeError("Database engine not initialized.")
    from src.models import produtos, ingredientes, receitas, imagens, tasks, vectors  # noqa: F401
    SQLModel.metadata.create_all(_engine)
