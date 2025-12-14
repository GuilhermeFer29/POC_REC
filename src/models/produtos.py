from pydantic import BaseModel, HttpUrl


class ProdutoOut(BaseModel):
    id: int
    nome: str
    tipo: str | None = None
    imagem: HttpUrl | None = None
    descricao: str | None = None
