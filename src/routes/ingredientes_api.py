"""
Rotas para integração com APIs externas de ingredientes.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.core.settings import Settings
from src.service.ingredientes_api import (
    IngredientesAPIService,
    USDAFood,
    OpenFoodFactsProduct,
    TheMealDBIngredient,
)


router = APIRouter(prefix="/ingredientes-api", tags=["ingredientes-api"])

settings = Settings()
api_service = IngredientesAPIService(usda_api_key=settings.usda_api_key)


class EnrichRequest(BaseModel):
    nome: str
    usda_fdc_id: int | None = None
    openfoodfacts_id: str | None = None


@router.get("/usda/search", response_model=list[USDAFood])
async def search_usda(
    query: str = Query(..., description="Termo de busca"),
    page_size: int = Query(10, ge=1, le=50),
):
    """Busca ingredientes no USDA FoodData Central."""
    if not settings.usda_api_key:
        raise HTTPException(
            status_code=503,
            detail="USDA API Key não configurada. Configure USDA_API_KEY no .env",
        )
    return await api_service.search_usda(query, page_size)


@router.get("/usda/{fdc_id}", response_model=USDAFood)
async def get_usda_food(fdc_id: int):
    """Obtém detalhes de um alimento do USDA pelo FDC ID."""
    if not settings.usda_api_key:
        raise HTTPException(
            status_code=503,
            detail="USDA API Key não configurada. Configure USDA_API_KEY no .env",
        )
    food = await api_service.get_usda_food(fdc_id)
    if not food:
        raise HTTPException(status_code=404, detail="Alimento não encontrado no USDA")
    return food


@router.get("/openfoodfacts/search", response_model=list[OpenFoodFactsProduct])
async def search_openfoodfacts(
    query: str = Query(..., description="Termo de busca"),
    page_size: int = Query(10, ge=1, le=50),
):
    """Busca produtos no Open Food Facts."""
    return await api_service.search_openfoodfacts(query, page_size)


@router.get("/openfoodfacts/{barcode}", response_model=OpenFoodFactsProduct)
async def get_openfoodfacts_product(barcode: str):
    """Obtém detalhes de um produto do Open Food Facts pelo código de barras."""
    product = await api_service.get_openfoodfacts_product(barcode)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado no Open Food Facts")
    return product


@router.get("/themealdb/ingredients", response_model=list[TheMealDBIngredient])
async def list_themealdb_ingredients():
    """Lista todos os ingredientes disponíveis no TheMealDB."""
    return await api_service.list_themealdb_ingredients()


@router.get("/themealdb/ingredient/{name}", response_model=TheMealDBIngredient)
async def get_themealdb_ingredient(name: str):
    """Busca um ingrediente específico no TheMealDB."""
    ingredient = await api_service.search_themealdb_ingredient(name)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingrediente não encontrado no TheMealDB")
    return ingredient


@router.post("/enrich")
async def enrich_ingredient(request: EnrichRequest):
    """
    Enriquece dados de um ingrediente buscando em múltiplas fontes.
    Combina dados do USDA (nutricionais), Open Food Facts (imagens) e TheMealDB.
    """
    return await api_service.enrich_ingredient(
        nome=request.nome,
        usda_fdc_id=request.usda_fdc_id,
        openfoodfacts_id=request.openfoodfacts_id,
    )
