import pytest
from unittest.mock import patch, MagicMock

from src.models.produtos import ProdutoClienteTable
from src.models.receitas import ReceitaTable, ReceitaCreate


class TestReceitasService:
    def test_criar_receita(self, test_session):
        from src.service.receitas_service import criar_receita

        produto = ProdutoClienteTable(nome_produto="Teste")
        test_session.add(produto)
        test_session.commit()
        test_session.refresh(produto)

        payload = ReceitaCreate(id_produto=produto.id_produto)
        receita = criar_receita(test_session, payload)

        assert receita.id_receita is not None
        assert receita.status == "pending"
        assert receita.id_produto == produto.id_produto

    def test_obter_receita_existente(self, test_session):
        from src.service.receitas_service import criar_receita, obter_receita

        produto = ProdutoClienteTable(nome_produto="Teste")
        test_session.add(produto)
        test_session.commit()
        test_session.refresh(produto)

        payload = ReceitaCreate(id_produto=produto.id_produto)
        receita_criada = criar_receita(test_session, payload)

        receita = obter_receita(test_session, receita_criada.id_receita)

        assert receita is not None
        assert receita.id_receita == receita_criada.id_receita

    def test_obter_receita_inexistente(self, test_session):
        from src.service.receitas_service import obter_receita

        receita = obter_receita(test_session, 99999)

        assert receita is None

    def test_atualizar_status(self, test_session):
        from src.service.receitas_service import criar_receita, atualizar_status

        produto = ProdutoClienteTable(nome_produto="Teste")
        test_session.add(produto)
        test_session.commit()
        test_session.refresh(produto)

        payload = ReceitaCreate(id_produto=produto.id_produto)
        receita = criar_receita(test_session, payload)

        assert receita.status == "pending"

        receita_atualizada = atualizar_status(test_session, receita.id_receita, "generating_recipe")

        assert receita_atualizada is not None
        assert receita_atualizada.status == "generating_recipe"

    def test_atualizar_status_receita_inexistente(self, test_session):
        from src.service.receitas_service import atualizar_status

        result = atualizar_status(test_session, 99999, "done")

        assert result is None

    def test_fluxo_completo_status(self, test_session):
        from src.service.receitas_service import criar_receita, atualizar_status

        produto = ProdutoClienteTable(nome_produto="Teste")
        test_session.add(produto)
        test_session.commit()
        test_session.refresh(produto)

        payload = ReceitaCreate(id_produto=produto.id_produto)
        receita = criar_receita(test_session, payload)

        estados = ["generating_recipe", "generating_images", "generating_html", "done"]

        for estado in estados:
            receita = atualizar_status(test_session, receita.id_receita, estado)
            assert receita.status == estado


class TestRAGService:
    def test_rag_service_init(self, mock_knowledge, mock_qdrant):
        with patch("src.service.rag_service.create_receitas_knowledge") as mock_rec, \
             patch("src.service.rag_service.create_fotografia_knowledge") as mock_foto:
            mock_rec.return_value = MagicMock()
            mock_foto.return_value = MagicMock()

            from src.service.rag_service import RAGService
            from src.core.settings import Settings

            settings = Settings()
            service = RAGService(settings)

            assert service.receitas_kb is not None
            assert service.fotografia_kb is not None

    def test_get_receitas_knowledge(self, mock_knowledge, mock_qdrant):
        with patch("src.service.rag_service.create_receitas_knowledge") as mock_rec, \
             patch("src.service.rag_service.create_fotografia_knowledge") as mock_foto:
            mock_kb = MagicMock()
            mock_rec.return_value = mock_kb
            mock_foto.return_value = MagicMock()

            from src.service.rag_service import RAGService
            from src.core.settings import Settings

            settings = Settings()
            service = RAGService(settings)

            kb = service.get_receitas_knowledge()

            assert kb == mock_kb

    def test_get_fotografia_knowledge(self, mock_knowledge, mock_qdrant):
        with patch("src.service.rag_service.create_receitas_knowledge") as mock_rec, \
             patch("src.service.rag_service.create_fotografia_knowledge") as mock_foto:
            mock_kb = MagicMock()
            mock_rec.return_value = MagicMock()
            mock_foto.return_value = mock_kb

            from src.service.rag_service import RAGService
            from src.core.settings import Settings

            settings = Settings()
            service = RAGService(settings)

            kb = service.get_fotografia_knowledge()

            assert kb == mock_kb
