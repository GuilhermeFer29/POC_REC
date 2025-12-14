import pytest
from unittest.mock import patch, MagicMock

from src.core.settings import Settings


class TestChefAgent:
    def test_create_chef_agent(self, mock_gemini, mock_knowledge, mock_qdrant):
        with patch("src.agents.chef.create_receitas_knowledge") as mock_kb:
            mock_kb.return_value = MagicMock()
            from src.agents.chef import create_chef_agent

            settings = Settings()
            agent = create_chef_agent(settings)

            assert agent is not None
            assert agent.name == "Chef"

    def test_chef_agent_with_custom_knowledge(self, mock_gemini):
        from src.agents.chef import create_chef_agent

        settings = Settings()
        custom_kb = MagicMock()

        agent = create_chef_agent(settings, knowledge=custom_kb)

        assert agent is not None
        assert agent.knowledge == custom_kb


class TestFotografoAgent:
    def test_create_fotografo_agent(self, mock_gemini, mock_nano_banana, mock_knowledge, mock_qdrant):
        with patch("src.agents.fotografo.create_fotografia_knowledge") as mock_kb:
            mock_kb.return_value = MagicMock()
            from src.agents.fotografo import create_fotografo_agent

            settings = Settings()
            agent = create_fotografo_agent(settings)

            assert agent is not None
            assert agent.name == "Fotografo"

    def test_fotografo_agent_has_tools(self, mock_gemini, mock_nano_banana, mock_knowledge, mock_qdrant):
        with patch("src.agents.fotografo.create_fotografia_knowledge") as mock_kb:
            mock_kb.return_value = MagicMock()
            from src.agents.fotografo import create_fotografo_agent

            settings = Settings()
            agent = create_fotografo_agent(settings)

            assert agent.tools is not None
            assert len(agent.tools) > 0


class TestDiagramadorAgent:
    def test_create_diagramador_agent(self, mock_gemini):
        from src.agents.diagramador import create_diagramador_agent

        settings = Settings()
        agent = create_diagramador_agent(settings)

        assert agent is not None
        assert agent.name == "Diagramador"


class TestOrquestrador:
    def test_orquestrador_init(self, mock_gemini, mock_nano_banana, mock_knowledge, mock_qdrant):
        with patch("src.agents.orquestrador.create_receitas_knowledge") as mock_rec_kb, \
             patch("src.agents.orquestrador.create_fotografia_knowledge") as mock_foto_kb:
            mock_rec_kb.return_value = MagicMock()
            mock_foto_kb.return_value = MagicMock()

            from src.agents.orquestrador import Orquestrador

            settings = Settings()
            orq = Orquestrador(settings)

            assert orq.chef is not None
            assert orq.fotografo is not None
            assert orq.diagramador is not None

    def test_orquestrador_executar_receita_nao_encontrada(
        self, test_session, mock_gemini, mock_nano_banana, mock_knowledge, mock_qdrant
    ):
        with patch("src.agents.orquestrador.create_receitas_knowledge") as mock_rec_kb, \
             patch("src.agents.orquestrador.create_fotografia_knowledge") as mock_foto_kb:
            mock_rec_kb.return_value = MagicMock()
            mock_foto_kb.return_value = MagicMock()

            from src.agents.orquestrador import Orquestrador
            from src.models.produtos import ProdutoClienteTable

            settings = Settings()
            orq = Orquestrador(settings)

            produto = ProdutoClienteTable(nome_produto="Teste")

            result = orq.executar(test_session, 99999, produto)

            assert result["status"] == "error"
            assert "não encontrada" in result.get("error", "")

    def test_orquestrador_executar_sucesso(
        self, test_session, mock_gemini, mock_nano_banana, mock_knowledge, mock_qdrant
    ):
        with patch("src.agents.orquestrador.create_receitas_knowledge") as mock_rec_kb, \
             patch("src.agents.orquestrador.create_fotografia_knowledge") as mock_foto_kb:
            mock_rec_kb.return_value = MagicMock()
            mock_foto_kb.return_value = MagicMock()

            from src.agents.orquestrador import Orquestrador
            from src.models.produtos import ProdutoClienteTable
            from src.models.receitas import ReceitaTable

            produto = ProdutoClienteTable(nome_produto="Leite Condensado")
            test_session.add(produto)
            test_session.commit()
            test_session.refresh(produto)

            receita = ReceitaTable(id_produto=produto.id_produto, status="pending")
            test_session.add(receita)
            test_session.commit()
            test_session.refresh(receita)

            settings = Settings()
            orq = Orquestrador(settings)

            orq.chef.run = MagicMock(return_value=MagicMock(
                content='{"ingredientes": [{"nome": "Leite"}], "modo_preparo": ["Passo 1"]}'
            ))
            orq.fotografo.run = MagicMock(return_value=MagicMock(content="image_url"))
            orq.diagramador.run = MagicMock(return_value=MagicMock(content="<html></html>"))

            result = orq.executar(test_session, receita.id_receita, produto)

            assert result["status"] == "done"
            assert result["receita_id"] == receita.id_receita
