from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Column, Text


class VectorTable(SQLModel, table=True):
    __tablename__ = "vectors"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_receita: int = Field(foreign_key="receitas.id_receita")
    kind: str  # ingrediente, step, image_ref
    qdrant_id: str
    payload: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class VectorCreate(BaseModel):
    id_receita: int
    kind: str
    qdrant_id: str
    payload: Optional[str] = None


class VectorOut(BaseModel):
    id: int
    id_receita: int
    kind: str
    qdrant_id: str
    payload: Optional[str] = None
    created_at: datetime
