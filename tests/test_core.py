import pytest
from unittest.mock import patch, MagicMock

from src.core.settings import Settings


class TestSettings:
    def test_settings_default_values(self):
        settings = Settings()

        assert settings.app_name == "POC Receitas"
        assert settings.env == "dev"
        assert settings.qdrant_port == 6333
        assert settings.gemini_model_text == "gemini-2.5-flash"
        assert settings.gemini_model_embed == "gemini-embedding-001"
        assert settings.agno_telemetry is False

    def test_settings_qdrant_url(self):
        settings = Settings()

        assert "qdrant" in settings.qdrant_url
        assert "6333" in settings.qdrant_url

    def test_settings_mysql_url(self):
        settings = Settings()

        assert "mysql" in settings.mysql_url
        assert "receitas" in settings.mysql_url


class TestDatabase:
    def test_init_engine(self):
        from src.core.db import init_engine

        settings = Settings()
        settings.mysql_url = "sqlite:///:memory:"

        engine = init_engine(settings)

        assert engine is not None

    def test_get_session_without_engine(self):
        from src.core import db

        original_engine = db._engine
        db._engine = None

        with pytest.raises(RuntimeError, match="not initialized"):
            list(db.get_session())

        db._engine = original_engine

    def test_create_db_and_tables(self, test_engine):
        from src.core.db import _engine
        from sqlmodel import SQLModel

        assert len(SQLModel.metadata.tables) > 0


class TestQdrantClient:
    def test_get_qdrant_client(self):
        with patch("src.core.qdrant_client.QdrantClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            from src.core.qdrant_client import get_qdrant_client

            settings = Settings()
            client = get_qdrant_client(settings)

            assert client is not None
            mock_client.assert_called_once()


class TestKnowledge:
    def test_create_knowledge_base(self, mock_qdrant):
        with patch("src.core.knowledge.GeminiEmbedder") as mock_embedder:
            mock_embedder.return_value = MagicMock()

            from src.core.knowledge import create_knowledge_base

            settings = Settings()
            kb = create_knowledge_base(settings, "test_collection")

            assert kb is not None

    def test_create_receitas_knowledge(self, mock_qdrant):
        with patch("src.core.knowledge.GeminiEmbedder") as mock_embedder:
            mock_embedder.return_value = MagicMock()

            from src.core.knowledge import create_receitas_knowledge

            settings = Settings()
            kb = create_receitas_knowledge(settings)

            assert kb is not None

    def test_create_fotografia_knowledge(self, mock_qdrant):
        with patch("src.core.knowledge.GeminiEmbedder") as mock_embedder:
            mock_embedder.return_value = MagicMock()

            from src.core.knowledge import create_fotografia_knowledge

            settings = Settings()
            kb = create_fotografia_knowledge(settings)

            assert kb is not None
