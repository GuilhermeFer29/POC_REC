import pytest
from unittest.mock import patch, MagicMock


class TestReceitasRoutes:
    def test_criar_receita_produto_inexistente(self, client):
        response = client.post(
            "/receitas",
            json={"id_produto": 99999},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Produto não encontrado"

    def test_criar_receita_sucesso(self, client):
        produto_response = client.post(
            "/produtos",
            json={"nome_produto": "Leite Condensado"},
        )
        produto_id = produto_response.json()["id"]

        with patch("src.routes.receitas._executar_orquestrador"):
            response = client.post(
                "/receitas",
                json={
                    "id_produto": produto_id,
                    "descricao_cliente": "Receita para sobremesa",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["status"] == "pending"

    def test_obter_receita_inexistente(self, client):
        response = client.get("/receitas/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Receita não encontrada"

    def test_obter_receita_existente(self, client):
        produto_response = client.post(
            "/produtos",
            json={"nome_produto": "Produto Teste"},
        )
        produto_id = produto_response.json()["id"]

        with patch("src.routes.receitas._executar_orquestrador"):
            create_response = client.post(
                "/receitas",
                json={"id_produto": produto_id},
            )
        receita_id = create_response.json()["id"]

        response = client.get(f"/receitas/{receita_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == receita_id
        assert data["status"] == "pending"

    def test_criar_receita_com_descricao(self, client):
        produto_response = client.post(
            "/produtos",
            json={"nome_produto": "Creme de Leite"},
        )
        produto_id = produto_response.json()["id"]

        with patch("src.routes.receitas._executar_orquestrador"):
            response = client.post(
                "/receitas",
                json={
                    "id_produto": produto_id,
                    "descricao_cliente": "Receita light para dieta",
                },
            )

        assert response.status_code == 201

    def test_criar_receita_sem_id_produto(self, client):
        response = client.post(
            "/receitas",
            json={"descricao_cliente": "Sem produto"},
        )
        assert response.status_code == 422
