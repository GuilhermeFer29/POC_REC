from typing import Optional

from pydantic import BaseModel, HttpUrl
from sqlmodel import Field, SQLModel


class ProdutoClienteTable(SQLModel, table=True):
    __tablename__ = "produtos_cliente"

    id_produto: Optional[int] = Field(default=None, primary_key=True)
    nome_produto: str
    tipo_produto: Optional[str] = None
    marca: Optional[str] = None
    imagem_produto: Optional[str] = None
    descricao: Optional[str] = None


class ProdutoCreate(BaseModel):
    nome_produto: str
    tipo_produto: str | None = None
    marca: str | None = None
    imagem_produto: HttpUrl | None = None
    descricao: str | None = None


class ProdutoOut(BaseModel):
    id: int
    nome: str
    tipo: str | None = None
    marca: str | None = None
    imagem: str | None = None
    descricao: str | None = None
