import json
import os
from pathlib import Path
from typing import Optional

from sqlmodel import Session

from src.core.settings import Settings
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

        try:
            atualizar_status(session, receita_id, "generating_recipe")
            resultado_chef = self._gerar_receita(produto, descricao_cliente)
            self._salvar_receita(session, receita, resultado_chef)

            atualizar_status(session, receita_id, "generating_images")
            imagens = self._gerar_imagens(
                receita_id, resultado_chef.get("modo_preparo", []), produto, refs_imagens
            )

            atualizar_status(session, receita_id, "generating_html")
            html = self._gerar_html(produto, resultado_chef, imagens)
            self._salvar_html(session, receita, html)

            atualizar_status(session, receita_id, "done")
            return {"status": "done", "receita_id": receita_id}

        except Exception as e:
            atualizar_status(session, receita_id, "error")
            return {"status": "error", "receita_id": receita_id, "error": str(e)}

    def _gerar_receita(self, produto: ProdutoClienteTable, descricao_cliente: Optional[str]) -> dict:
        prompt = f"""Crie uma receita para o produto: {produto.nome_produto}.
Tipo do produto: {produto.tipo_produto or 'não especificado'}.
Descrição: {produto.descricao or descricao_cliente or 'não especificada'}.

Retorne APENAS um JSON válido com:
- "ingredientes": lista de objetos com "nome", "quantidade", "unidade"
- "modo_preparo": lista de strings com os passos ordenados
"""
        response = self.chef.run(prompt)
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
    ) -> list:
        imagens = []
        media_dir = Path(f"media/receitas/{receita_id}")
        media_dir.mkdir(parents=True, exist_ok=True)

        for i, passo in enumerate(passos):
            prompt = f"""Fotografia profissional de alimento mostrando o passo: {passo}
Produto: {produto.nome_produto}
Mantenha consistência visual do produto em todas as imagens.
Estilo: fotografia gastronômica profissional, iluminação natural."""

            response = self.fotografo.run(prompt)
            image_path = f"media/receitas/{receita_id}/step_{i}.png"
            imagens.append({
                "step_index": i,
                "url": image_path,
                "content": getattr(response, "content", ""),
            })
        return imagens

    def _gerar_html(self, produto: ProdutoClienteTable, resultado_chef: dict, imagens: list) -> str:
        ingredientes = resultado_chef.get("ingredientes", [])
        passos = resultado_chef.get("modo_preparo", [])
        imagens_urls = [img.get("url", "") for img in imagens]

        prompt = f"""Monte uma micro página HTML de receita com:
- Título: Receita com {produto.nome_produto}
- Carrossel de imagens do passo a passo: {imagens_urls}
- Seção de ingredientes ordenados: {ingredientes}
- Seção de modo de preparo ordenado: {passos}
- Destaque para a imagem do produto

Retorne APENAS o HTML válido, sem markdown."""

        response = self.diagramador.run(prompt)
        content = getattr(response, "content", "")
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
