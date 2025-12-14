import pytest


class TestIngredientesRoutes:
    def test_criar_ingrediente(self, client):
        response = client.post(
            "/ingredientes",
            json={
                "nome_singular": "Ovo",
                "nome_plural": "Ovos",
                "tipo_ingrediente": "Proteína",
                "descricao": "Ovo de galinha",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["nome_singular"] == "Ovo"
        assert data["nome_plural"] == "Ovos"

    def test_listar_ingredientes_vazio(self, client):
        response = client.get("/ingredientes")
        assert response.status_code == 200
        assert response.json() == []

    def test_listar_ingredientes_com_dados(self, client):
        client.post(
            "/ingredientes",
            json={"nome_singular": "Sal", "nome_plural": "Sais"},
        )
        client.post(
            "/ingredientes",
            json={"nome_singular": "Açúcar", "nome_plural": "Açúcares"},
        )

        response = client.get("/ingredientes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_obter_ingrediente_existente(self, client):
        create_response = client.post(
            "/ingredientes",
            json={"nome_singular": "Farinha", "nome_plural": "Farinhas"},
        )
        ingrediente_id = create_response.json()["id"]

        response = client.get(f"/ingredientes/{ingrediente_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ingrediente_id
        assert data["nome_singular"] == "Farinha"

    def test_obter_ingrediente_inexistente(self, client):
        response = client.get("/ingredientes/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Ingrediente não encontrado"

    def test_criar_ingrediente_sem_nome(self, client):
        response = client.post(
            "/ingredientes",
            json={"nome_plural": "Ovos"},
        )
        assert response.status_code == 422

    def test_criar_ingrediente_campos_opcionais(self, client):
        response = client.post(
            "/ingredientes",
            json={"nome_singular": "Leite"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["nome_singular"] == "Leite"
        assert data["nome_plural"] is None
