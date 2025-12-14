from pydantic import BaseModel, HttpUrl


class IngredienteOut(BaseModel):
    id: int
    nome_singular: str
    nome_plural: str | None = None
    tipo: str | None = None
    imagem: HttpUrl | None = None
    descricao: str | None = None
