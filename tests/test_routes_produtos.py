import pytest


class TestProdutosRoutes:
    def test_criar_produto(self, client):
        response = client.post(
            "/produtos",
            json={
                "nome_produto": "Leite Condensado",
                "tipo_produto": "Laticínio",
                "descricao": "Leite condensado tradicional",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["nome"] == "Leite Condensado"
        assert data["tipo"] == "Laticínio"

    def test_listar_produtos_vazio(self, client):
        response = client.get("/produtos")
        assert response.status_code == 200
        assert response.json() == []

    def test_listar_produtos_com_dados(self, client):
        client.post(
            "/produtos",
            json={"nome_produto": "Produto 1", "tipo_produto": "Tipo A"},
        )
        client.post(
            "/produtos",
            json={"nome_produto": "Produto 2", "tipo_produto": "Tipo B"},
        )

        response = client.get("/produtos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_obter_produto_existente(self, client):
        create_response = client.post(
            "/produtos",
            json={"nome_produto": "Produto Teste"},
        )
        produto_id = create_response.json()["id"]

        response = client.get(f"/produtos/{produto_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == produto_id
        assert data["nome"] == "Produto Teste"

    def test_obter_produto_inexistente(self, client):
        response = client.get("/produtos/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Produto não encontrado"

    def test_criar_produto_sem_nome(self, client):
        response = client.post(
            "/produtos",
            json={"tipo_produto": "Tipo"},
        )
        assert response.status_code == 422

    def test_criar_produto_campos_opcionais(self, client):
        response = client.post(
            "/produtos",
            json={"nome_produto": "Produto Simples"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "Produto Simples"
        assert data["tipo"] is None
