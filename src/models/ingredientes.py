from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class IngredienteTable(SQLModel, table=True):
    __tablename__ = "ingredientes"

    id_ingrediente: Optional[int] = Field(default=None, primary_key=True)
    nome_singular: str
    nome_plural: Optional[str] = None
    tipo_ingrediente: Optional[str] = None
    imagem_ingrediente: Optional[str] = Field(default=None, sa_column=Column(Text))
    descricao: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    usda_fdc_id: Optional[int] = Field(default=None, description="ID no USDA FoodData Central")
    openfoodfacts_id: Optional[str] = Field(default=None, description="ID no Open Food Facts")
    foodon_id: Optional[str] = Field(default=None, description="ID na ontologia FoodOn")
    
    calorias: Optional[float] = Field(default=None, description="kcal por 100g")
    proteinas: Optional[float] = Field(default=None, description="g por 100g")
    carboidratos: Optional[float] = Field(default=None, description="g por 100g")
    gorduras: Optional[float] = Field(default=None, description="g por 100g")
    fibras: Optional[float] = Field(default=None, description="g por 100g")


class IngredienteOut(BaseModel):
    id: int
    nome_singular: str
    nome_plural: str | None = None
    tipo: str | None = None
    imagem: str | None = None
    descricao: str | None = None
    usda_fdc_id: int | None = None
    openfoodfacts_id: str | None = None
    foodon_id: str | None = None
    calorias: float | None = None
    proteinas: float | None = None
    carboidratos: float | None = None
    gorduras: float | None = None
    fibras: float | None = None


class IngredienteCreate(BaseModel):
    nome_singular: str
    nome_plural: str | None = None
    tipo_ingrediente: str | None = None
    imagem_ingrediente: str | None = None
    descricao: str | None = None
    usda_fdc_id: int | None = None
    openfoodfacts_id: str | None = None
    foodon_id: str | None = None
    calorias: float | None = None
    proteinas: float | None = None
    carboidratos: float | None = None
    gorduras: float | None = None
    fibras: float | None = None
