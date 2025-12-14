"""
Testes para o serviço de integração com APIs externas de ingredientes.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.service.ingredientes_api import (
    IngredientesAPIService,
    USDAFood,
    OpenFoodFactsProduct,
    TheMealDBIngredient,
)


class TestIngredientesAPIService:
    @pytest.fixture
    def service(self):
        return IngredientesAPIService(usda_api_key="test_key")

    @pytest.fixture
    def service_no_key(self):
        return IngredientesAPIService(usda_api_key=None)

    @pytest.mark.asyncio
    async def test_search_usda_without_key(self, service_no_key):
        result = await service_no_key.search_usda("chicken")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_usda_success(self, service):
        mock_response = {
            "foods": [
                {
                    "fdcId": 123456,
                    "description": "Chicken, breast, raw",
                    "foodCategory": "Poultry",
                    "foodNutrients": [
                        {"nutrientId": 1008, "value": 120},
                        {"nutrientId": 1003, "value": 22},
                        {"nutrientId": 1005, "value": 0},
                        {"nutrientId": 1004, "value": 2.5},
                        {"nutrientId": 1079, "value": 0},
                    ],
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.return_value = MagicMock(
                status_code=200, json=lambda: mock_response
            )

            result = await service.search_usda("chicken")

            assert len(result) == 1
            assert result[0].fdc_id == 123456
            assert result[0].description == "Chicken, breast, raw"
            assert result[0].calories == 120
            assert result[0].protein == 22

    @pytest.mark.asyncio
    async def test_search_openfoodfacts_success(self, service):
        mock_response = {
            "products": [
                {
                    "code": "123456789",
                    "product_name": "Leite Integral",
                    "image_url": "https://example.com/milk.jpg",
                    "categories": "Laticínios",
                    "nova_group": 1,
                    "nutriments": {
                        "energy-kcal_100g": 65,
                        "proteins_100g": 3.2,
                        "carbohydrates_100g": 4.8,
                        "fat_100g": 3.5,
                        "fiber_100g": 0,
                    },
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.return_value = MagicMock(
                status_code=200, json=lambda: mock_response
            )

            result = await service.search_openfoodfacts("leite")

            assert len(result) == 1
            assert result[0].code == "123456789"
            assert result[0].product_name == "Leite Integral"
            assert result[0].energy_kcal == 65

    @pytest.mark.asyncio
    async def test_list_themealdb_ingredients(self, service):
        mock_response = {
            "meals": [
                {"idIngredient": "1", "strIngredient": "Chicken", "strDescription": "Poultry"},
                {"idIngredient": "2", "strIngredient": "Salmon", "strDescription": "Fish"},
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.return_value = MagicMock(
                status_code=200, json=lambda: mock_response
            )

            result = await service.list_themealdb_ingredients()

            assert len(result) == 2
            assert result[0].name == "Chicken"
            assert result[1].name == "Salmon"
            assert "themealdb.com/images/ingredients/Chicken.png" in result[0].image_url

    @pytest.mark.asyncio
    async def test_enrich_ingredient(self, service):
        with patch.object(service, "search_usda", new_callable=AsyncMock) as mock_usda, \
             patch.object(service, "search_openfoodfacts", new_callable=AsyncMock) as mock_off, \
             patch.object(service, "search_themealdb_ingredient", new_callable=AsyncMock) as mock_mealdb:

            mock_usda.return_value = [
                USDAFood(
                    fdc_id=123,
                    description="Chicken",
                    calories=120,
                    protein=22,
                    carbohydrates=0,
                    fat=2.5,
                    fiber=0,
                )
            ]
            mock_off.return_value = [
                OpenFoodFactsProduct(
                    code="456",
                    product_name="Chicken",
                    image_url="https://example.com/chicken.jpg",
                )
            ]
            mock_mealdb.return_value = None

            result = await service.enrich_ingredient("chicken")

            assert result["nome"] == "chicken"
            assert result["usda_fdc_id"] == 123
            assert result["openfoodfacts_id"] == "456"
            assert result["calorias"] == 120
            assert result["proteinas"] == 22
            assert result["imagem_url"] == "https://example.com/chicken.jpg"


class TestUSDAFood:
    def test_usda_food_model(self):
        food = USDAFood(
            fdc_id=123,
            description="Test Food",
            food_category="Test Category",
            calories=100,
            protein=10,
            carbohydrates=20,
            fat=5,
            fiber=2,
        )
        assert food.fdc_id == 123
        assert food.description == "Test Food"


class TestOpenFoodFactsProduct:
    def test_openfoodfacts_product_model(self):
        product = OpenFoodFactsProduct(
            code="123456789",
            product_name="Test Product",
            image_url="https://example.com/image.jpg",
            nova_group=1,
        )
        assert product.code == "123456789"
        assert product.product_name == "Test Product"


class TestTheMealDBIngredient:
    def test_themealdb_ingredient_model(self):
        ingredient = TheMealDBIngredient(
            id="1",
            name="Chicken",
            description="Poultry",
            image_url="https://example.com/chicken.png",
        )
        assert ingredient.id == "1"
        assert ingredient.name == "Chicken"
