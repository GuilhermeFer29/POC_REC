"""
Serviço para integração com TheMealDB API para receitas.
Útil para alimentar o RAG com receitas de exemplo.
"""

import httpx
from pydantic import BaseModel


class MealDBRecipe(BaseModel):
    id: str
    name: str
    category: str | None = None
    area: str | None = None
    instructions: str | None = None
    image_url: str | None = None
    youtube_url: str | None = None
    ingredients: list[dict] = []
    tags: str | None = None


class TheMealDBService:
    BASE_URL = "https://www.themealdb.com/api/json/v1/1"

    async def search_recipes(self, query: str) -> list[MealDBRecipe]:
        """Busca receitas por nome."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/search.php",
                params={"s": query},
            )

            if response.status_code != 200:
                return []

            data = response.json()
            meals = data.get("meals") or []

            return [self._parse_meal(meal) for meal in meals]

    async def get_recipe_by_id(self, meal_id: str) -> MealDBRecipe | None:
        """Obtém uma receita específica pelo ID."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/lookup.php",
                params={"i": meal_id},
            )

            if response.status_code != 200:
                return None

            data = response.json()
            meals = data.get("meals")

            if not meals:
                return None

            return self._parse_meal(meals[0])

    async def get_random_recipe(self) -> MealDBRecipe | None:
        """Obtém uma receita aleatória."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.BASE_URL}/random.php")

            if response.status_code != 200:
                return None

            data = response.json()
            meals = data.get("meals")

            if not meals:
                return None

            return self._parse_meal(meals[0])

    async def list_categories(self) -> list[str]:
        """Lista todas as categorias de receitas."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.BASE_URL}/list.php?c=list")

            if response.status_code != 200:
                return []

            data = response.json()
            meals = data.get("meals") or []

            return [m.get("strCategory") for m in meals if m.get("strCategory")]

    async def list_areas(self) -> list[str]:
        """Lista todas as áreas/cozinhas (ex: Italian, Mexican)."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.BASE_URL}/list.php?a=list")

            if response.status_code != 200:
                return []

            data = response.json()
            meals = data.get("meals") or []

            return [m.get("strArea") for m in meals if m.get("strArea")]

    async def filter_by_category(self, category: str) -> list[MealDBRecipe]:
        """Filtra receitas por categoria."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/filter.php",
                params={"c": category},
            )

            if response.status_code != 200:
                return []

            data = response.json()
            meals = data.get("meals") or []

            return [
                MealDBRecipe(
                    id=m.get("idMeal", ""),
                    name=m.get("strMeal", ""),
                    image_url=m.get("strMealThumb"),
                )
                for m in meals
            ]

    async def filter_by_ingredient(self, ingredient: str) -> list[MealDBRecipe]:
        """Filtra receitas por ingrediente principal."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/filter.php",
                params={"i": ingredient},
            )

            if response.status_code != 200:
                return []

            data = response.json()
            meals = data.get("meals") or []

            return [
                MealDBRecipe(
                    id=m.get("idMeal", ""),
                    name=m.get("strMeal", ""),
                    image_url=m.get("strMealThumb"),
                )
                for m in meals
            ]

    def _parse_meal(self, meal: dict) -> MealDBRecipe:
        """Converte resposta da API para MealDBRecipe."""
        ingredients = []
        for i in range(1, 21):
            ingredient = meal.get(f"strIngredient{i}")
            measure = meal.get(f"strMeasure{i}")
            if ingredient and ingredient.strip():
                ingredients.append({
                    "ingredient": ingredient.strip(),
                    "measure": measure.strip() if measure else "",
                })

        return MealDBRecipe(
            id=meal.get("idMeal", ""),
            name=meal.get("strMeal", ""),
            category=meal.get("strCategory"),
            area=meal.get("strArea"),
            instructions=meal.get("strInstructions"),
            image_url=meal.get("strMealThumb"),
            youtube_url=meal.get("strYoutube"),
            ingredients=ingredients,
            tags=meal.get("strTags"),
        )

    def recipe_to_rag_content(self, recipe: MealDBRecipe) -> str:
        """Converte uma receita para texto formatado para RAG."""
        lines = [
            f"# {recipe.name}",
            "",
        ]

        if recipe.category:
            lines.append(f"**Categoria:** {recipe.category}")
        if recipe.area:
            lines.append(f"**Cozinha:** {recipe.area}")
        if recipe.tags:
            lines.append(f"**Tags:** {recipe.tags}")

        lines.append("")
        lines.append("## Ingredientes")
        for ing in recipe.ingredients:
            lines.append(f"- {ing['measure']} {ing['ingredient']}")

        lines.append("")
        lines.append("## Modo de Preparo")
        if recipe.instructions:
            lines.append(recipe.instructions)

        return "\n".join(lines)
