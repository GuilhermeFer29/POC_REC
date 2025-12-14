import pytest
import io
import os
import shutil
from pathlib import Path


class TestUploadRoutes:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        test_media = Path("media_test")
        test_media.mkdir(parents=True, exist_ok=True)
        yield
        if test_media.exists():
            shutil.rmtree(test_media)

    def test_upload_imagem_produto(self, client):
        file_content = b"fake image content"
        files = {"file": ("test_image.png", io.BytesIO(file_content), "image/png")}

        response = client.post("/upload/produto/1", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "produto_1.png"
        assert "media/produtos/1" in data["path"]
        assert "sucesso" in data["message"]

    def test_upload_imagem_passo_receita(self, client):
        file_content = b"fake step image"
        files = {"file": ("step.png", io.BytesIO(file_content), "image/png")}

        response = client.post("/upload/receita/1/step/0", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "step_0.png"
        assert "media/receitas/1" in data["path"]

    def test_upload_arquivo_rag_receitas(self, client):
        file_content = b"Livro de receitas brasileiras..."
        files = {"file": ("receitas.pdf", io.BytesIO(file_content), "application/pdf")}

        response = client.post("/upload/rag/receitas", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "receitas.pdf"
        assert "rag/receitas" in data["path"]

    def test_upload_arquivo_rag_fotografia(self, client):
        file_content = b"Livro de fotografia gastronomica..."
        files = {"file": ("fotografia.pdf", io.BytesIO(file_content), "application/pdf")}

        response = client.post("/upload/rag/fotografia", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "fotografia.pdf"
        assert "rag/fotografia" in data["path"]

    def test_upload_rag_tipo_invalido(self, client):
        file_content = b"content"
        files = {"file": ("file.pdf", io.BytesIO(file_content), "application/pdf")}

        response = client.post("/upload/rag/invalido", files=files)
        assert response.status_code == 400
        assert "receitas" in response.json()["detail"] or "fotografia" in response.json()["detail"]

    def test_listar_arquivos_produtos(self, client):
        file_content = b"fake image"
        files = {"file": ("test.png", io.BytesIO(file_content), "image/png")}
        client.post("/upload/produto/1", files=files)

        response = client.get("/upload/listar/produtos")
        assert response.status_code == 200
        data = response.json()
        assert data["tipo"] == "produtos"
        assert isinstance(data["arquivos"], list)

    def test_listar_arquivos_receitas(self, client):
        response = client.get("/upload/listar/receitas")
        assert response.status_code == 200
        data = response.json()
        assert data["tipo"] == "receitas"

    def test_listar_arquivos_rag(self, client):
        response = client.get("/upload/listar/rag")
        assert response.status_code == 200
        data = response.json()
        assert data["tipo"] == "rag"

    def test_listar_arquivos_tipo_invalido(self, client):
        response = client.get("/upload/listar/invalido")
        assert response.status_code == 400
