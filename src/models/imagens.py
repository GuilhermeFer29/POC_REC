from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl
from sqlmodel import Field, SQLModel, Column, Text


class ImagemTable(SQLModel, table=True):
    __tablename__ = "imagens"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_receita: int = Field(foreign_key="receitas.id_receita")
    step_index: int
    url: str
    prompt_meta: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    seed: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class ImagemCreate(BaseModel):
    id_receita: int
    step_index: int
    url: str
    prompt_meta: Optional[str] = None
    seed: Optional[str] = None


class ImagemOut(BaseModel):
    id: int
    id_receita: int
    step_index: int
    url: str
    prompt_meta: Optional[str] = None
    seed: Optional[str] = None
    created_at: datetime
