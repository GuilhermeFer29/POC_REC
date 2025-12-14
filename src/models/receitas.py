from typing import Any, List, Optional

from pydantic import BaseModel, HttpUrl


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
