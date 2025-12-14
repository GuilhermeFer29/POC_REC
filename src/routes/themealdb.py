"""
Rotas para integração com TheMealDB API.
"""

from fastapi import APIRouter, HTTPException, Query

from src.service.themealdb_service import TheMealDBService, MealDBRecipe


router = APIRouter(prefix="/themealdb", tags=["themealdb"])

service = TheMealDBService()


@router.get("/search", response_model=list[MealDBRecipe])
async def search_recipes(query: str = Query(..., description="Termo de busca")):
    """Busca receitas por nome no TheMealDB."""
    return await service.search_recipes(query)


@router.get("/recipe/{meal_id}", response_model=MealDBRecipe)
async def get_recipe(meal_id: str):
    """Obtém uma receita específica pelo ID."""
    recipe = await service.get_recipe_by_id(meal_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    return recipe


@router.get("/random", response_model=MealDBRecipe)
async def get_random_recipe():
    """Obtém uma receita aleatória."""
    recipe = await service.get_random_recipe()
    if not recipe:
        raise HTTPException(status_code=503, detail="Não foi possível obter receita aleatória")
    return recipe


@router.get("/categories", response_model=list[str])
async def list_categories():
    """Lista todas as categorias de receitas."""
    return await service.list_categories()


@router.get("/areas", response_model=list[str])
async def list_areas():
    """Lista todas as áreas/cozinhas disponíveis."""
    return await service.list_areas()


@router.get("/filter/category/{category}", response_model=list[MealDBRecipe])
async def filter_by_category(category: str):
    """Filtra receitas por categoria."""
    return await service.filter_by_category(category)


@router.get("/filter/ingredient/{ingredient}", response_model=list[MealDBRecipe])
async def filter_by_ingredient(ingredient: str):
    """Filtra receitas por ingrediente principal."""
    return await service.filter_by_ingredient(ingredient)


@router.get("/recipe/{meal_id}/rag-content")
async def get_recipe_rag_content(meal_id: str):
    """Obtém o conteúdo de uma receita formatado para RAG."""
    recipe = await service.get_recipe_by_id(meal_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    
    content = service.recipe_to_rag_content(recipe)
    return {
        "meal_id": meal_id,
        "name": recipe.name,
        "content": content,
    }
