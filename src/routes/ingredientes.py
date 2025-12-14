from fastapi import APIRouter

from src.models.ingredientes import IngredienteOut

router = APIRouter(prefix="/ingredientes", tags=["ingredientes"])


@router.get("", response_model=list[IngredienteOut])
def listar_ingredientes():
    return []
