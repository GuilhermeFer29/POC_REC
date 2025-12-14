from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.vectordb.qdrant import Qdrant

from src.core.settings import Settings


def create_knowledge_base(settings: Settings, collection_name: str = "receitas") -> Knowledge:
    vector_db = Qdrant(
        collection=collection_name,
        url=settings.qdrant_url,
        embedder=GeminiEmbedder(
            id=settings.gemini_model_embed,
            api_key=settings.gemini_api_key,
        ),
    )

    knowledge = Knowledge(
        name="Receitas Knowledge Base",
        description="Base de conhecimento para receitas, ingredientes e referências de fotografia",
        vector_db=vector_db,
    )

    return knowledge


def create_receitas_knowledge(settings: Settings) -> Knowledge:
    return create_knowledge_base(settings, "receitas")


def create_fotografia_knowledge(settings: Settings) -> Knowledge:
    return create_knowledge_base(settings, "fotografia")
