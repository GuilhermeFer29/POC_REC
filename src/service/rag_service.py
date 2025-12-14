import asyncio
from typing import Optional

from agno.knowledge.knowledge import Knowledge

from src.core.settings import Settings
from src.core.knowledge import create_receitas_knowledge, create_fotografia_knowledge


class RAGService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.receitas_kb = create_receitas_knowledge(settings)
        self.fotografia_kb = create_fotografia_knowledge(settings)

    def add_receita_content(self, name: str, content: str, metadata: Optional[dict] = None):
        asyncio.run(
            self.receitas_kb.add_content_async(
                name=name,
                content=content,
                metadata=metadata or {"tipo": "receita"},
            )
        )

    def add_receita_from_url(self, name: str, url: str, metadata: Optional[dict] = None):
        asyncio.run(
            self.receitas_kb.add_content_async(
                name=name,
                url=url,
                metadata=metadata or {"tipo": "receita"},
            )
        )

    def add_fotografia_content(self, name: str, content: str, metadata: Optional[dict] = None):
        asyncio.run(
            self.fotografia_kb.add_content_async(
                name=name,
                content=content,
                metadata=metadata or {"tipo": "fotografia"},
            )
        )

    def add_fotografia_from_url(self, name: str, url: str, metadata: Optional[dict] = None):
        asyncio.run(
            self.fotografia_kb.add_content_async(
                name=name,
                url=url,
                metadata=metadata or {"tipo": "fotografia"},
            )
        )

    def search_receitas(self, query: str, num_documents: int = 5) -> list:
        return self.receitas_kb.search(query=query, num_documents=num_documents)

    def search_fotografia(self, query: str, num_documents: int = 5) -> list:
        return self.fotografia_kb.search(query=query, num_documents=num_documents)

    def get_receitas_knowledge(self) -> Knowledge:
        return self.receitas_kb

    def get_fotografia_knowledge(self) -> Knowledge:
        return self.fotografia_kb
