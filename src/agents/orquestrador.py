import json
import logging
import os
from pathlib import Path
from typing import Optional
from uuid import uuid4

from sqlmodel import Session

from src.core.settings import Settings

logger = logging.getLogger(__name__)
from src.core.knowledge import create_receitas_knowledge, create_fotografia_knowledge
from src.agents.chef import create_chef_agent
from src.agents.fotografo import create_fotografo_agent
from src.agents.diagramador import create_diagramador_agent
from src.service.receitas_service import atualizar_status, obter_receita
from src.models.receitas import ReceitaTable
from src.models.produtos import ProdutoClienteTable


class Orquestrador:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.receitas_kb = create_receitas_knowledge(settings)
        self.fotografia_kb = create_fotografia_knowledge(settings)
        self.chef = create_chef_agent(settings, knowledge=self.receitas_kb)
        self.fotografo = create_fotografo_agent(settings, knowledge=self.fotografia_kb)
        self.diagramador = create_diagramador_agent(settings)

    def executar(
        self,
        session: Session,
        receita_id: int,
        produto: ProdutoClienteTable,
        descricao_cliente: Optional[str] = None,
        refs_imagens: Optional[list] = None,
    ) -> dict:
        receita = obter_receita(session, receita_id)
        if not receita:
            return {"error": "Receita não encontrada", "status": "error"}

        # Session ID compartilhado entre todos os agentes para manter contexto
        shared_session_id = f"receita_{receita_id}_{uuid4().hex[:8]}"
        logger.info(f"[Orquestrador] Session ID compartilhado: {shared_session_id}")

        try:
            logger.info(f"[Orquestrador] Iniciando receita {receita_id}")
            atualizar_status(session, receita_id, "generating_recipe")
            logger.info(f"[Orquestrador] Chamando Chef...")
            resultado_chef = self._gerar_receita(produto, descricao_cliente, shared_session_id)
            logger.info(f"[Orquestrador] Chef retornou: {len(resultado_chef.get('modo_preparo', []))} passos")
            self._salvar_receita(session, receita, resultado_chef)

            atualizar_status(session, receita_id, "generating_images")
            logger.info(f"[Orquestrador] Chamando Fotógrafo para {len(resultado_chef.get('modo_preparo', []))} passos...")
            imagens = self._gerar_imagens(
                receita_id, resultado_chef.get("modo_preparo", []), produto, refs_imagens, shared_session_id
            )
            logger.info(f"[Orquestrador] Fotógrafo retornou {len(imagens)} imagens")

            atualizar_status(session, receita_id, "generating_html")
            logger.info(f"[Orquestrador] Chamando Diagramador...")
            html = self._gerar_html(produto, resultado_chef, imagens, shared_session_id)
            logger.info(f"[Orquestrador] Diagramador retornou HTML com {len(html)} chars")
            self._salvar_html(session, receita, html)

            atualizar_status(session, receita_id, "done")
            logger.info(f"[Orquestrador] Receita {receita_id} concluída!")
            return {"status": "done", "receita_id": receita_id}

        except Exception as e:
            logger.error(f"[Orquestrador] Erro na receita {receita_id}: {e}")
            atualizar_status(session, receita_id, "error")
            return {"status": "error", "receita_id": receita_id, "error": str(e)}

    def _gerar_receita(self, produto: ProdutoClienteTable, descricao_cliente: Optional[str], session_id: str) -> dict:
        prompt = f"""Crie uma receita para o produto: {produto.nome_produto}.
Tipo do produto: {produto.tipo_produto or 'não especificado'}.
Descrição: {produto.descricao or descricao_cliente or 'não especificada'}.

Retorne APENAS um JSON válido com:
- "ingredientes": lista de objetos com "nome", "quantidade", "unidade"
- "modo_preparo": lista de strings com os passos ordenados
"""
        response = self.chef.run(prompt, session_id=session_id)
        try:
            content = getattr(response, "content", "")
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except (json.JSONDecodeError, AttributeError, IndexError):
            return {"ingredientes": [], "modo_preparo": []}

    def _salvar_receita(self, session: Session, receita: ReceitaTable, resultado: dict):
        receita.json_ingredientes = json.dumps(resultado.get("ingredientes", []), ensure_ascii=False)
        receita.json_modo_preparo = json.dumps(resultado.get("modo_preparo", []), ensure_ascii=False)
        session.add(receita)
        session.commit()
        session.refresh(receita)

    def _gerar_imagens(
        self,
        receita_id: int,
        passos: list,
        produto: ProdutoClienteTable,
        refs_imagens: Optional[list] = None,
        session_id: str = None,
    ) -> list:
        import time
        
        imagens = []
        media_dir = Path(f"media/receitas/{receita_id}")
        media_dir.mkdir(parents=True, exist_ok=True)

        for i, passo in enumerate(passos):
            logger.info(f"[Fotógrafo] Gerando imagem {i+1}/{len(passos)} para: {passo[:50]}...")
            prompt = f"""Fotografia profissional de alimento mostrando o passo: {passo}
Produto: {produto.nome_produto}
Mantenha consistência visual do produto em todas as imagens.
Estilo: fotografia gastronômica profissional, iluminação natural."""

            response = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.fotografo.run(prompt, session_id=session_id)
                    logger.info(f"[Fotógrafo] Imagem {i+1} gerada com sucesso")
                    break
                except Exception as e:
                    logger.error(f"[Fotógrafo] Tentativa {attempt+1}/{max_retries} falhou: {e}")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        logger.info(f"[Fotógrafo] Aguardando {wait_time}s antes de tentar novamente...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"[Fotógrafo] Todas as tentativas falharam para imagem {i+1}")
            
            image_path = f"media/receitas/{receita_id}/step_{i}.png"
            
            # Salvar imagem no disco se foi gerada
            if response and hasattr(response, 'images') and response.images:
                for img in response.images:
                    if hasattr(img, 'content') and img.content:
                        with open(image_path, 'wb') as f:
                            f.write(img.content)
                        logger.info(f"[Fotógrafo] Imagem salva em: {image_path}")
                        break
            
            imagens.append({
                "step_index": i,
                "url": image_path,
                "content": getattr(response, "content", "") if response else "",
            })
        return imagens

    def _gerar_html(self, produto: ProdutoClienteTable, resultado_chef: dict, imagens: list, session_id: str = None) -> str:
        """Coordena a geração de HTML pelo agente Diagramador."""
        ingredientes = resultado_chef.get("ingredientes", [])
        passos = resultado_chef.get("modo_preparo", [])
        
        # Usar caminhos absolutos do servidor
        imagens_urls = [f"/{img.get('url', '')}" for img in imagens]

        # Montar prompt com os dados para o Diagramador
        prompt = f"""Gere o HTML da receita com os seguintes dados:

PRODUTO: {produto.nome_produto}

IMAGENS (URLs para o carrossel):
{imagens_urls}

INGREDIENTES:
{ingredientes}

MODO DE PREPARO:
{passos}

Gere o HTML completo com carrossel funcional seguindo suas instruções."""

        response = self.diagramador.run(prompt, session_id=session_id)
        content = getattr(response, "content", "")
        
        # Limpar markdown se presente
        if "```html" in content:
            content = content.split("```html")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return content.strip()

    def _salvar_html(self, session: Session, receita: ReceitaTable, html: str):
        receita.content_html = html
        session.add(receita)
        session.commit()
        session.refresh(receita)
