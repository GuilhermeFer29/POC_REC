from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Column, Text


class TaskTable(SQLModel, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_receita: int = Field(foreign_key="receitas.id_receita")
    type: str  # recipe, image, html
    status: str = Field(default="pending")  # pending, running, done, error
    error: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class TaskCreate(BaseModel):
    id_receita: int
    type: str
    status: str = "pending"


class TaskOut(BaseModel):
    id: int
    id_receita: int
    type: str
    status: str
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
