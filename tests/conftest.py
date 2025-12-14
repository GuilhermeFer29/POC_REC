import os
import pytest
from typing import Generator
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

os.environ["GEMINI_API_KEY"] = "test-api-key"
os.environ["AGNO_TELEMETRY"] = "false"

from src.main import app
from src.core.db import get_session
from src.core.settings import Settings


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def test_session(test_engine) -> Generator[Session, None, None]:
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="function")
def client(test_engine) -> Generator[TestClient, None, None]:
    def get_test_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def settings():
    return Settings()


@pytest.fixture
def mock_gemini():
    with patch("agno.models.google.Gemini") as mock:
        mock_instance = MagicMock()
        mock_instance.run.return_value = MagicMock(
            content='{"ingredientes": [{"nome": "Leite", "quantidade": "1", "unidade": "litro"}], "modo_preparo": ["Aquecer o leite", "Adicionar açúcar"]}'
        )
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_nano_banana():
    with patch("agno.tools.nano_banana.NanoBananaTools") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_knowledge():
    with patch("agno.knowledge.knowledge.Knowledge") as mock:
        mock_instance = MagicMock()
        mock_instance.search.return_value = []
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_qdrant():
    with patch("agno.vectordb.qdrant.Qdrant") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock
