import pytest
from unittest.mock import patch, MagicMock


class TestRAGRoutes:
    @pytest.fixture(autouse=True)
    def mock_rag_service(self):
        with patch("src.routes.rag.rag_service") as mock:
            mock.add_receita_content = MagicMock()
            mock.add_receita_from_url = MagicMock()
            mock.add_fotografia_content = MagicMock()
            mock.add_fotografia_from_url = MagicMock()
            mock.search_receitas = MagicMock(return_value=[{"text": "resultado 1"}])
            mock.search_fotografia = MagicMock(return_value=[{"text": "resultado 2"}])
            yield mock

    def test_add_receita_content(self, client, mock_rag_service):
        response = client.post(
            "/rag/receitas/content",
            json={
                "name": "Receita Teste",
                "content": "Ingredientes: leite, açúcar...",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "Receita Teste" in data["message"]

    def test_add_receita_from_url(self, client, mock_rag_service):
        response = client.post(
            "/rag/receitas/url",
            json={
                "name": "Livro de Receitas",
                "url": "https://example.com/receitas.pdf",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_search_receitas(self, client, mock_rag_service):
        response = client.post(
            "/rag/receitas/search",
            json={
                "query": "como fazer bolo",
                "num_documents": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_add_fotografia_content(self, client, mock_rag_service):
        response = client.post(
            "/rag/fotografia/content",
            json={
                "name": "Técnicas de Fotografia",
                "content": "Iluminação natural é essencial...",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "fotografia" in data["message"]

    def test_add_fotografia_from_url(self, client, mock_rag_service):
        response = client.post(
            "/rag/fotografia/url",
            json={
                "name": "Manual de Fotografia",
                "url": "https://example.com/fotografia.pdf",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_search_fotografia(self, client, mock_rag_service):
        response = client.post(
            "/rag/fotografia/search",
            json={
                "query": "iluminação para alimentos",
                "num_documents": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    def test_add_content_sem_nome(self, client):
        response = client.post(
            "/rag/receitas/content",
            json={"content": "Conteúdo sem nome"},
        )
        assert response.status_code == 422

    def test_add_content_sem_conteudo(self, client):
        response = client.post(
            "/rag/receitas/content",
            json={"name": "Nome sem conteúdo"},
        )
        assert response.status_code == 422

    def test_search_sem_query(self, client):
        response = client.post(
            "/rag/receitas/search",
            json={"num_documents": 5},
        )
        assert response.status_code == 422
