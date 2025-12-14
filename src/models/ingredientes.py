from typing import Optional

from pydantic import BaseModel, HttpUrl
from sqlmodel import Field, SQLModel


class IngredienteTable(SQLModel, table=True):
    __tablename__ = "ingredientes"

    id_ingrediente: Optional[int] = Field(default=None, primary_key=True)
    nome_singular: str
    nome_plural: Optional[str] = None
    tipo_ingrediente: Optional[str] = None
    imagem_ingrediente: Optional[str] = None
    descricao: Optional[str] = None


class IngredienteOut(BaseModel):
    id: int
    nome_singular: str
    nome_plural: str | None = None
    tipo: str | None = None
    imagem: HttpUrl | None = None
    descricao: str | None = None


class IngredienteCreate(BaseModel):
    nome_singular: str
    nome_plural: str | None = None
    tipo_ingrediente: str | None = None
    imagem_ingrediente: HttpUrl | None = None
    descricao: str | None = None
