from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, HttpUrl
from sqlmodel import Field, SQLModel, Column, Text


class ReceitaTable(SQLModel, table=True):
    __tablename__ = "receitas"

    id_receita: Optional[int] = Field(default=None, primary_key=True)
    id_produto: int = Field(foreign_key="produtos_cliente.id_produto")
    status: str = Field(default="pending")
    json_ingredientes: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    json_modo_preparo: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    content_html: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    link_wp: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class ReceitaCreate(BaseModel):
    id_produto: int
    descricao_cliente: Optional[str] = None
    refs_imagens: Optional[List[HttpUrl]] = None


class ImagemPasso(BaseModel):
    step_index: int
    url: HttpUrl


class ReceitaOut(BaseModel):
    id: int
    status: str
    json_ingredientes: Any | None = None
    json_modo_preparo: Any | None = None
    imagens: List[ImagemPasso] = []
    content_html: str | None = None
    link_wp: HttpUrl | None = None
