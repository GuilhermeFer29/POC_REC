"""
Serviço de integração com APIs externas de ingredientes:
- USDA FoodData Central (dados nutricionais)
- Open Food Facts (produtos industrializados + imagens)
- TheMealDB (receitas e ingredientes)
"""

import httpx
from typing import Optional
from pydantic import BaseModel


class USDANutrient(BaseModel):
    nutrient_id: int
    name: str
    amount: float
    unit: str


class USDAFood(BaseModel):
    fdc_id: int
    description: str
    food_category: str | None = None
    calories: float | None = None
    protein: float | None = None
    carbohydrates: float | None = None
    fat: float | None = None
    fiber: float | None = None


class OpenFoodFactsProduct(BaseModel):
    code: str
    product_name: str | None = None
    image_url: str | None = None
    categories: str | None = None
    nova_group: int | None = None
    energy_kcal: float | None = None
    proteins: float | None = None
    carbohydrates: float | None = None
    fat: float | None = None
    fiber: float | None = None


class TheMealDBIngredient(BaseModel):
    id: str
    name: str
    description: str | None = None
    image_url: str | None = None


class IngredientesAPIService:
    USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    OPENFOODFACTS_BASE_URL = "https://world.openfoodfacts.org/api/v2"
    THEMEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1"

    def __init__(self, usda_api_key: str | None = None):
        self.usda_api_key = usda_api_key
        self.client = httpx.Client(timeout=30.0)

    async def search_usda(self, query: str, page_size: int = 10) -> list[USDAFood]:
        """Busca ingredientes no USDA FoodData Central."""
        if not self.usda_api_key:
            return []

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.USDA_BASE_URL}/foods/search",
                params={
                    "api_key": self.usda_api_key,
                    "query": query,
                    "pageSize": page_size,
                    "dataType": ["Foundation", "SR Legacy"],
                },
            )

            if response.status_code != 200:
                return []

            data = response.json()
            foods = []

            for food in data.get("foods", []):
                nutrients = {n["nutrientId"]: n["value"] for n in food.get("foodNutrients", [])}
                
                foods.append(USDAFood(
                    fdc_id=food["fdcId"],
                    description=food["description"],
                    food_category=food.get("foodCategory"),
                    calories=nutrients.get(1008),
                    protein=nutrients.get(1003),
                    carbohydrates=nutrients.get(1005),
                    fat=nutrients.get(1004),
                    fiber=nutrients.get(1079),
                ))

            return foods

    async def get_usda_food(self, fdc_id: int) -> USDAFood | None:
        """Obtém detalhes de um alimento específico do USDA."""
        if not self.usda_api_key:
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.USDA_BASE_URL}/food/{fdc_id}",
                params={"api_key": self.usda_api_key},
            )

            if response.status_code != 200:
                return None

            food = response.json()
            nutrients = {}
            for n in food.get("foodNutrients", []):
                nutrient = n.get("nutrient", {})
                nutrients[nutrient.get("id")] = n.get("amount", 0)

            return USDAFood(
                fdc_id=food["fdcId"],
                description=food["description"],
                food_category=food.get("foodCategory", {}).get("description"),
                calories=nutrients.get(1008),
                protein=nutrients.get(1003),
                carbohydrates=nutrients.get(1005),
                fat=nutrients.get(1004),
                fiber=nutrients.get(1079),
            )

    async def search_openfoodfacts(self, query: str, page_size: int = 10) -> list[OpenFoodFactsProduct]:
        """Busca produtos no Open Food Facts."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.OPENFOODFACTS_BASE_URL}/search",
                params={
                    "search_terms": query,
                    "page_size": page_size,
                    "fields": "code,product_name,image_url,categories,nova_group,nutriments",
                },
            )

            if response.status_code != 200:
                return []

            data = response.json()
            products = []

            for product in data.get("products", []):
                nutriments = product.get("nutriments", {})
                products.append(OpenFoodFactsProduct(
                    code=product.get("code", ""),
                    product_name=product.get("product_name"),
                    image_url=product.get("image_url"),
                    categories=product.get("categories"),
                    nova_group=product.get("nova_group"),
                    energy_kcal=nutriments.get("energy-kcal_100g"),
                    proteins=nutriments.get("proteins_100g"),
                    carbohydrates=nutriments.get("carbohydrates_100g"),
                    fat=nutriments.get("fat_100g"),
                    fiber=nutriments.get("fiber_100g"),
                ))

            return products

    async def get_openfoodfacts_product(self, barcode: str) -> OpenFoodFactsProduct | None:
        """Obtém detalhes de um produto específico do Open Food Facts."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.OPENFOODFACTS_BASE_URL}/product/{barcode}",
                params={"fields": "code,product_name,image_url,categories,nova_group,nutriments"},
            )

            if response.status_code != 200:
                return None

            data = response.json()
            if data.get("status") != 1:
                return None

            product = data.get("product", {})
            nutriments = product.get("nutriments", {})

            return OpenFoodFactsProduct(
                code=product.get("code", barcode),
                product_name=product.get("product_name"),
                image_url=product.get("image_url"),
                categories=product.get("categories"),
                nova_group=product.get("nova_group"),
                energy_kcal=nutriments.get("energy-kcal_100g"),
                proteins=nutriments.get("proteins_100g"),
                carbohydrates=nutriments.get("carbohydrates_100g"),
                fat=nutriments.get("fat_100g"),
                fiber=nutriments.get("fiber_100g"),
            )

    async def list_themealdb_ingredients(self) -> list[TheMealDBIngredient]:
        """Lista todos os ingredientes do TheMealDB."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.THEMEALDB_BASE_URL}/list.php?i=list")

            if response.status_code != 200:
                return []

            data = response.json()
            ingredients = []

            for ing in data.get("meals", []) or []:
                ing_id = ing.get("idIngredient", "")
                ing_name = ing.get("strIngredient", "")
                
                ingredients.append(TheMealDBIngredient(
                    id=ing_id,
                    name=ing_name,
                    description=ing.get("strDescription"),
                    image_url=f"https://www.themealdb.com/images/ingredients/{ing_name}.png" if ing_name else None,
                ))

            return ingredients

    async def search_themealdb_ingredient(self, name: str) -> TheMealDBIngredient | None:
        """Busca um ingrediente específico no TheMealDB."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.THEMEALDB_BASE_URL}/search.php",
                params={"i": name},
            )

            if response.status_code != 200:
                return None

            data = response.json()
            ingredients = data.get("meals")
            
            if not ingredients:
                return None

            ing = ingredients[0]
            ing_name = ing.get("strIngredient", name)

            return TheMealDBIngredient(
                id=ing.get("idIngredient", ""),
                name=ing_name,
                description=ing.get("strDescription"),
                image_url=f"https://www.themealdb.com/images/ingredients/{ing_name}.png",
            )

    async def enrich_ingredient(
        self,
        nome: str,
        usda_fdc_id: int | None = None,
        openfoodfacts_id: str | None = None,
    ) -> dict:
        """
        Enriquece dados de um ingrediente buscando em múltiplas fontes.
        Retorna um dicionário com dados consolidados.
        """
        result = {
            "nome": nome,
            "usda_fdc_id": usda_fdc_id,
            "openfoodfacts_id": openfoodfacts_id,
            "calorias": None,
            "proteinas": None,
            "carboidratos": None,
            "gorduras": None,
            "fibras": None,
            "imagem_url": None,
            "categoria": None,
        }

        if usda_fdc_id:
            usda_food = await self.get_usda_food(usda_fdc_id)
            if usda_food:
                result["calorias"] = usda_food.calories
                result["proteinas"] = usda_food.protein
                result["carboidratos"] = usda_food.carbohydrates
                result["gorduras"] = usda_food.fat
                result["fibras"] = usda_food.fiber
                result["categoria"] = usda_food.food_category
        elif self.usda_api_key:
            usda_foods = await self.search_usda(nome, page_size=1)
            if usda_foods:
                usda_food = usda_foods[0]
                result["usda_fdc_id"] = usda_food.fdc_id
                result["calorias"] = usda_food.calories
                result["proteinas"] = usda_food.protein
                result["carboidratos"] = usda_food.carbohydrates
                result["gorduras"] = usda_food.fat
                result["fibras"] = usda_food.fiber
                result["categoria"] = usda_food.food_category

        if openfoodfacts_id:
            off_product = await self.get_openfoodfacts_product(openfoodfacts_id)
            if off_product:
                result["imagem_url"] = off_product.image_url
                if not result["calorias"]:
                    result["calorias"] = off_product.energy_kcal
                    result["proteinas"] = off_product.proteins
                    result["carboidratos"] = off_product.carbohydrates
                    result["gorduras"] = off_product.fat
                    result["fibras"] = off_product.fiber
        else:
            off_products = await self.search_openfoodfacts(nome, page_size=1)
            if off_products:
                off_product = off_products[0]
                result["openfoodfacts_id"] = off_product.code
                result["imagem_url"] = off_product.image_url
                if not result["calorias"]:
                    result["calorias"] = off_product.energy_kcal
                    result["proteinas"] = off_product.proteins
                    result["carboidratos"] = off_product.carbohydrates
                    result["gorduras"] = off_product.fat
                    result["fibras"] = off_product.fiber

        if not result["imagem_url"]:
            mealdb_ing = await self.search_themealdb_ingredient(nome)
            if mealdb_ing:
                result["imagem_url"] = mealdb_ing.image_url

        return result
