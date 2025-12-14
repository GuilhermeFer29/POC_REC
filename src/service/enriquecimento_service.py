"""
Serviço de enriquecimento automático do banco de dados e RAG.
Combina dados de USDA, Open Food Facts, TheMealDB para popular:
- Tabela de ingredientes com dados nutricionais
- Base de conhecimento RAG com receitas e informações culinárias
- Download e persistência de imagens em media/ (volume Docker)
"""

import asyncio
from typing import Optional

from sqlmodel import Session, select

from src.core.settings import Settings
from src.core.db import get_session
from src.models.ingredientes import IngredienteTable
from src.service.ingredientes_api import IngredientesAPIService
from src.service.themealdb_service import TheMealDBService
from src.service.rag_service import RAGService
from src.service.image_downloader import ImageDownloader


class EnriquecimentoService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.ingredientes_api = IngredientesAPIService(usda_api_key=settings.usda_api_key)
        self.themealdb = TheMealDBService()
        self.rag_service = RAGService(settings)
        self.image_downloader = ImageDownloader(base_path="media")

    async def enriquecer_ingrediente_por_nome(
        self, session: Session, nome: str
    ) -> IngredienteTable:
        """
        Busca ou cria um ingrediente e enriquece com dados das APIs externas.
        """
        stmt = select(IngredienteTable).where(IngredienteTable.nome_singular == nome)
        ingrediente = session.exec(stmt).first()

        if not ingrediente:
            ingrediente = IngredienteTable(nome_singular=nome)
            session.add(ingrediente)
            session.commit()
            session.refresh(ingrediente)

        dados = await self.ingredientes_api.enrich_ingredient(nome)

        ingrediente.usda_fdc_id = dados.get("usda_fdc_id")
        ingrediente.openfoodfacts_id = dados.get("openfoodfacts_id")
        ingrediente.calorias = dados.get("calorias")
        ingrediente.proteinas = dados.get("proteinas")
        ingrediente.carboidratos = dados.get("carboidratos")
        ingrediente.gorduras = dados.get("gorduras")
        ingrediente.fibras = dados.get("fibras")
        ingrediente.tipo_ingrediente = dados.get("categoria")

        imagem_url = dados.get("imagem_url")
        if imagem_url:
            local_path = await self.image_downloader.download_ingrediente_image(
                url=imagem_url,
                ingrediente_id=ingrediente.id_ingrediente,
                nome=nome,
            )
            ingrediente.imagem_ingrediente = local_path or imagem_url
        else:
            ingrediente.imagem_ingrediente = None

        session.add(ingrediente)
        session.commit()
        session.refresh(ingrediente)

        return ingrediente

    async def importar_ingredientes_themealdb(self, session: Session) -> list[IngredienteTable]:
        """
        Importa todos os ingredientes do TheMealDB para o banco de dados.
        """
        ingredientes_mealdb = await self.themealdb.list_themealdb_ingredients()
        ingredientes_criados = []

        for ing in ingredientes_mealdb:
            stmt = select(IngredienteTable).where(
                IngredienteTable.nome_singular == ing.name
            )
            existente = session.exec(stmt).first()

            if not existente:
                novo = IngredienteTable(
                    nome_singular=ing.name,
                    descricao=ing.description,
                )
                session.add(novo)
                session.commit()
                session.refresh(novo)
                
                if ing.image_url:
                    local_path = await self.image_downloader.download_ingrediente_image(
                        url=ing.image_url,
                        ingrediente_id=novo.id_ingrediente,
                        nome=ing.name,
                    )
                    novo.imagem_ingrediente = local_path or ing.image_url
                    session.add(novo)
                    session.commit()
                    session.refresh(novo)
                
                ingredientes_criados.append(novo)

        if ingredientes_criados:
            session.commit()
            for ing in ingredientes_criados:
                session.refresh(ing)

        return ingredientes_criados

    async def enriquecer_todos_ingredientes(self, session: Session) -> dict:
        """
        Enriquece todos os ingredientes do banco com dados das APIs externas.
        """
        ingredientes = session.exec(select(IngredienteTable)).all()
        enriquecidos = 0
        erros = []

        for ing in ingredientes:
            try:
                await self.enriquecer_ingrediente_por_nome(session, ing.nome_singular)
                enriquecidos += 1
            except Exception as e:
                erros.append({"ingrediente": ing.nome_singular, "erro": str(e)})

        return {
            "total": len(ingredientes),
            "enriquecidos": enriquecidos,
            "erros": erros,
        }

    async def popular_rag_com_receitas_themealdb(
        self, categorias: list[str] | None = None, limite_por_categoria: int = 10
    ) -> dict:
        """
        Popula a base de conhecimento RAG com receitas do TheMealDB.
        """
        if not categorias:
            categorias = await self.themealdb.list_categories()

        receitas_adicionadas = 0
        erros = []

        for categoria in categorias:
            try:
                receitas = await self.themealdb.filter_by_category(categoria)

                for receita_resumo in receitas[:limite_por_categoria]:
                    try:
                        receita_completa = await self.themealdb.get_recipe_by_id(
                            receita_resumo.id
                        )
                        if receita_completa:
                            if receita_completa.image_url:
                                local_path = await self.image_downloader.download_image(
                                    url=receita_completa.image_url,
                                    subdir="receitas_themealdb",
                                    prefix=f"rec_{receita_completa.id}",
                                )
                                if local_path:
                                    receita_completa.image_url = local_path
                            
                            conteudo = self.themealdb.recipe_to_rag_content(receita_completa)
                            self.rag_service.add_receita_content(
                                name=receita_completa.name,
                                content=conteudo,
                            )
                            receitas_adicionadas += 1
                    except Exception as e:
                        erros.append({
                            "receita": receita_resumo.name,
                            "erro": str(e),
                        })
            except Exception as e:
                erros.append({"categoria": categoria, "erro": str(e)})

        return {
            "categorias_processadas": len(categorias),
            "receitas_adicionadas": receitas_adicionadas,
            "erros": erros,
        }

    async def popular_rag_com_receitas_por_ingrediente(
        self, ingrediente: str, limite: int = 5
    ) -> dict:
        """
        Busca receitas que usam um ingrediente específico e adiciona ao RAG.
        """
        receitas = await self.themealdb.filter_by_ingredient(ingrediente)
        adicionadas = 0
        erros = []

        for receita_resumo in receitas[:limite]:
            try:
                receita_completa = await self.themealdb.get_recipe_by_id(receita_resumo.id)
                if receita_completa:
                    if receita_completa.image_url:
                        local_path = await self.image_downloader.download_image(
                            url=receita_completa.image_url,
                            subdir="receitas_themealdb",
                            prefix=f"rec_{receita_completa.id}",
                        )
                        if local_path:
                            receita_completa.image_url = local_path
                    
                    conteudo = self.themealdb.recipe_to_rag_content(receita_completa)
                    self.rag_service.add_receita_content(
                        name=receita_completa.name,
                        content=conteudo,
                    )
                    adicionadas += 1
            except Exception as e:
                erros.append({"receita": receita_resumo.name, "erro": str(e)})

        return {
            "ingrediente": ingrediente,
            "receitas_encontradas": len(receitas),
            "receitas_adicionadas": adicionadas,
            "erros": erros,
        }

    def gerar_conteudo_ingrediente_para_rag(self, ingrediente: IngredienteTable) -> str:
        """
        Gera conteúdo textual de um ingrediente para adicionar ao RAG.
        """
        lines = [
            f"# {ingrediente.nome_singular}",
            "",
        ]

        if ingrediente.nome_plural:
            lines.append(f"**Plural:** {ingrediente.nome_plural}")
        if ingrediente.tipo_ingrediente:
            lines.append(f"**Categoria:** {ingrediente.tipo_ingrediente}")
        if ingrediente.descricao:
            lines.append(f"**Descrição:** {ingrediente.descricao}")

        lines.append("")
        lines.append("## Informações Nutricionais (por 100g)")

        if ingrediente.calorias:
            lines.append(f"- **Calorias:** {ingrediente.calorias} kcal")
        if ingrediente.proteinas:
            lines.append(f"- **Proteínas:** {ingrediente.proteinas}g")
        if ingrediente.carboidratos:
            lines.append(f"- **Carboidratos:** {ingrediente.carboidratos}g")
        if ingrediente.gorduras:
            lines.append(f"- **Gorduras:** {ingrediente.gorduras}g")
        if ingrediente.fibras:
            lines.append(f"- **Fibras:** {ingrediente.fibras}g")

        lines.append("")
        lines.append("## Referências")
        if ingrediente.usda_fdc_id:
            lines.append(f"- USDA FDC ID: {ingrediente.usda_fdc_id}")
        if ingrediente.openfoodfacts_id:
            lines.append(f"- Open Food Facts: {ingrediente.openfoodfacts_id}")

        return "\n".join(lines)

    async def popular_rag_com_ingredientes(self, session: Session) -> dict:
        """
        Adiciona todos os ingredientes do banco ao RAG com informações nutricionais.
        """
        ingredientes = session.exec(select(IngredienteTable)).all()
        adicionados = 0

        for ing in ingredientes:
            if ing.calorias or ing.proteinas:
                conteudo = self.gerar_conteudo_ingrediente_para_rag(ing)
                self.rag_service.add_receita_content(
                    name=f"Ingrediente: {ing.nome_singular}",
                    content=conteudo,
                )
                adicionados += 1

        return {
            "total_ingredientes": len(ingredientes),
            "adicionados_ao_rag": adicionados,
        }
