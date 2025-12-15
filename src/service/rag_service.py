import asyncio
import logging
import nest_asyncio
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
from agno.knowledge.knowledge import Knowledge

from src.core.settings import Settings
from src.core.knowledge import create_receitas_knowledge, create_fotografia_knowledge

nest_asyncio.apply()
logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.receitas_kb = create_receitas_knowledge(settings)
        self.fotografia_kb = create_fotografia_knowledge(settings)

    def _run_async(self, coro):
        """Executa coroutine de forma segura, mesmo dentro de contexto async."""
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    def add_receita_content(self, name: str, content: str, metadata: Optional[dict] = None):
        self._run_async(
            self.receitas_kb.add_content_async(
                name=name,
                text_content=content,
                metadata=metadata or {"tipo": "receita"},
            )
        )

    def add_receita_from_url(self, name: str, url: str, metadata: Optional[dict] = None):
        self._run_async(
            self.receitas_kb.add_content_async(
                name=name,
                url=url,
                metadata=metadata or {"tipo": "receita"},
            )
        )

    def add_fotografia_content(self, name: str, content: str, metadata: Optional[dict] = None):
        self._run_async(
            self.fotografia_kb.add_content_async(
                name=name,
                text_content=content,
                metadata=metadata or {"tipo": "fotografia"},
            )
        )

    def add_fotografia_from_url(self, name: str, url: str, metadata: Optional[dict] = None):
        self._run_async(
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

    def process_pdf_file(self, file_path: str, tipo: str) -> dict:
        """
        Processa um arquivo PDF e adiciona ao RAG.
        
        Args:
            file_path: Caminho do arquivo PDF
            tipo: 'receitas' ou 'fotografia'
            
        Returns:
            dict com status e número de chunks processados
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        if not path.suffix.lower() == '.pdf':
            raise ValueError(f"Arquivo deve ser PDF: {file_path}")
        
        logger.info(f"Processando PDF: {path.name} para RAG {tipo}")
        
        try:
            # Usar PyMuPDF (fitz) para ler o PDF
            doc = fitz.open(str(path))
            
            kb = self.receitas_kb if tipo == "receitas" else self.fotografia_kb
            chunks_added = 0
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                content = page.get_text()
                
                if content and len(content.strip()) > 50:  # Ignorar páginas muito vazias
                    doc_name = f"{path.stem}_page_{page_num + 1}"
                    
                    self._run_async(
                        kb.add_content_async(
                            name=doc_name,
                            text_content=content,
                            metadata={
                                "tipo": tipo,
                                "source_file": path.name,
                                "page": page_num + 1,
                            },
                        )
                    )
                    chunks_added += 1
            
            doc.close()
            logger.info(f"PDF processado: {chunks_added} chunks adicionados ao RAG {tipo}")
            return {"status": "success", "chunks": chunks_added, "file": path.name}
            
        except Exception as e:
            logger.error(f"Erro ao processar PDF {path.name}: {e}")
            raise
