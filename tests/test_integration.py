import pytest
from unittest.mock import patch, MagicMock


class TestIntegrationFluxoCompleto:
    def test_fluxo_criar_produto_e_receita(self, client):
        response = client.post(
            "/produtos",
            json={
                "nome_produto": "Leite Condensado Moça",
                "tipo_produto": "Laticínio",
                "descricao": "Leite condensado tradicional",
            },
        )
        assert response.status_code == 201
        produto = response.json()
        produto_id = produto["id"]

        with patch("src.routes.receitas._executar_orquestrador"):
            response = client.post(
                "/receitas",
                json={
                    "id_produto": produto_id,
                    "descricao_cliente": "Receita de brigadeiro",
                },
            )
        assert response.status_code == 201
        receita = response.json()
        assert receita["status"] == "pending"

        response = client.get(f"/receitas/{receita['id']}")
        assert response.status_code == 200

    def test_fluxo_criar_ingredientes_e_listar(self, client):
        ingredientes = [
            {"nome_singular": "Leite", "nome_plural": "Leites", "tipo_ingrediente": "Laticínio"},
            {"nome_singular": "Açúcar", "nome_plural": "Açúcares", "tipo_ingrediente": "Doce"},
            {"nome_singular": "Chocolate", "nome_plural": "Chocolates", "tipo_ingrediente": "Doce"},
        ]

        for ing in ingredientes:
            response = client.post("/ingredientes", json=ing)
            assert response.status_code == 201

        response = client.get("/ingredientes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "db_url" in data
        assert "qdrant_host" in data


class TestIntegrationRAG:
    @pytest.fixture(autouse=True)
    def mock_rag(self):
        with patch("src.routes.rag.rag_service") as mock:
            mock.add_receita_content = MagicMock()
            mock.add_fotografia_content = MagicMock()
            mock.search_receitas = MagicMock(return_value=[
                {"text": "Receita de bolo de chocolate", "score": 0.95}
            ])
            mock.search_fotografia = MagicMock(return_value=[
                {"text": "Iluminação lateral para alimentos", "score": 0.88}
            ])
            yield mock

    def test_fluxo_adicionar_e_buscar_receitas(self, client, mock_rag):
        response = client.post(
            "/rag/receitas/content",
            json={
                "name": "Livro de Receitas",
                "content": "Receita de bolo de chocolate: ingredientes...",
            },
        )
        assert response.status_code == 200

        response = client.post(
            "/rag/receitas/search",
            json={"query": "bolo de chocolate", "num_documents": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0

    def test_fluxo_adicionar_e_buscar_fotografia(self, client, mock_rag):
        response = client.post(
            "/rag/fotografia/content",
            json={
                "name": "Manual de Fotografia",
                "content": "Iluminação lateral para alimentos...",
            },
        )
        assert response.status_code == 200

        response = client.post(
            "/rag/fotografia/search",
            json={"query": "iluminação alimentos", "num_documents": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0


class TestIntegrationUpload:
    def test_fluxo_upload_imagem_produto(self, client):
        response = client.post(
            "/produtos",
            json={"nome_produto": "Produto com Imagem"},
        )
        produto_id = response.json()["id"]

        import io
        file_content = b"fake image bytes"
        files = {"file": ("produto.png", io.BytesIO(file_content), "image/png")}

        response = client.post(f"/upload/produto/{produto_id}", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "produto" in data["path"]

    def test_fluxo_upload_arquivo_rag(self, client):
        import io
        file_content = b"Conteudo do livro de receitas..."
        files = {"file": ("livro_receitas.pdf", io.BytesIO(file_content), "application/pdf")}

        response = client.post("/upload/rag/receitas", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "rag/receitas" in data["path"]


class TestIntegrationWebSocket:
    def test_websocket_receita_inexistente(self, client):
        with client.websocket_connect("/receitas/stream/99999") as websocket:
            data = websocket.receive_json()
            assert "error" in data or data.get("status") == "pending"

    def test_websocket_receita_existente(self, client):
        response = client.post(
            "/produtos",
            json={"nome_produto": "Produto WS"},
        )
        produto_id = response.json()["id"]

        with patch("src.routes.receitas._executar_orquestrador"):
            response = client.post(
                "/receitas",
                json={"id_produto": produto_id},
            )
        receita_id = response.json()["id"]

        with client.websocket_connect(f"/receitas/stream/{receita_id}") as websocket:
            data = websocket.receive_json()
            assert "status" in data
            assert data["receita_id"] == receita_id
