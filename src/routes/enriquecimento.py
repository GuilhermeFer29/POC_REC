"""
Rotas para enriquecimento automático do banco de dados e RAG.
"""

from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sqlmodel import Session
from pydantic import BaseModel

from src.core.db import get_session
from src.core.settings import Settings
from src.service.enriquecimento_service import EnriquecimentoService


router = APIRouter(prefix="/enriquecimento", tags=["enriquecimento"])

settings = Settings()
enriquecimento_service = EnriquecimentoService(settings)


class EnriquecerIngredienteRequest(BaseModel):
    nome: str


class PopularRAGRequest(BaseModel):
    categorias: list[str] | None = None
    limite_por_categoria: int = 10


class PopularRAGIngredienteRequest(BaseModel):
    ingrediente: str
    limite: int = 5


@router.post("/ingrediente")
async def enriquecer_ingrediente(
    request: EnriquecerIngredienteRequest,
    session: Session = Depends(get_session),
):
    """
    Enriquece um ingrediente específico com dados do USDA, Open Food Facts e TheMealDB.
    Cria o ingrediente se não existir.
    """
    ingrediente = await enriquecimento_service.enriquecer_ingrediente_por_nome(
        session, request.nome
    )
    return {
        "status": "ok",
        "ingrediente": {
            "id": ingrediente.id_ingrediente,
            "nome": ingrediente.nome_singular,
            "usda_fdc_id": ingrediente.usda_fdc_id,
            "openfoodfacts_id": ingrediente.openfoodfacts_id,
            "calorias": ingrediente.calorias,
            "proteinas": ingrediente.proteinas,
            "carboidratos": ingrediente.carboidratos,
            "gorduras": ingrediente.gorduras,
            "fibras": ingrediente.fibras,
            "imagem": ingrediente.imagem_ingrediente,
            "tipo": ingrediente.tipo_ingrediente,
        },
    }


@router.post("/importar-themealdb")
async def importar_ingredientes_themealdb(
    session: Session = Depends(get_session),
):
    """
    Importa todos os ingredientes do TheMealDB para o banco de dados local.
    """
    ingredientes = await enriquecimento_service.importar_ingredientes_themealdb(session)
    return {
        "status": "ok",
        "ingredientes_importados": len(ingredientes),
        "ingredientes": [
            {"id": i.id_ingrediente, "nome": i.nome_singular}
            for i in ingredientes
        ],
    }


@router.post("/enriquecer-todos")
async def enriquecer_todos_ingredientes(
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    """
    Enriquece todos os ingredientes do banco com dados das APIs externas.
    Executa em background devido ao tempo de processamento.
    """
    async def _enriquecer():
        return await enriquecimento_service.enriquecer_todos_ingredientes(session)

    background_tasks.add_task(_enriquecer)
    return {
        "status": "processing",
        "message": "Enriquecimento iniciado em background. Consulte os ingredientes para ver o progresso.",
    }


@router.post("/rag/receitas-themealdb")
async def popular_rag_receitas_themealdb(
    request: PopularRAGRequest,
    background_tasks: BackgroundTasks,
):
    """
    Popula a base de conhecimento RAG com receitas do TheMealDB.
    Executa em background devido ao tempo de processamento.
    """
    async def _popular():
        return await enriquecimento_service.popular_rag_com_receitas_themealdb(
            categorias=request.categorias,
            limite_por_categoria=request.limite_por_categoria,
        )

    background_tasks.add_task(_popular)
    return {
        "status": "processing",
        "message": f"Populando RAG com receitas. Categorias: {request.categorias or 'todas'}",
    }


@router.post("/rag/receitas-por-ingrediente")
async def popular_rag_receitas_por_ingrediente(request: PopularRAGIngredienteRequest):
    """
    Busca receitas que usam um ingrediente específico e adiciona ao RAG.
    """
    resultado = await enriquecimento_service.popular_rag_com_receitas_por_ingrediente(
        ingrediente=request.ingrediente,
        limite=request.limite,
    )
    return {
        "status": "ok",
        **resultado,
    }


@router.post("/rag/ingredientes")
async def popular_rag_ingredientes(session: Session = Depends(get_session)):
    """
    Adiciona todos os ingredientes do banco ao RAG com informações nutricionais.
    """
    resultado = await enriquecimento_service.popular_rag_com_ingredientes(session)
    return {
        "status": "ok",
        **resultado,
    }


@router.get("/status")
async def status_enriquecimento(session: Session = Depends(get_session)):
    """
    Retorna estatísticas do banco de dados e RAG.
    """
    from sqlmodel import func, select
    from src.models.ingredientes import IngredienteTable

    total = session.exec(select(func.count(IngredienteTable.id_ingrediente))).one()
    com_usda = session.exec(
        select(func.count(IngredienteTable.id_ingrediente)).where(
            IngredienteTable.usda_fdc_id.isnot(None)
        )
    ).one()
    com_off = session.exec(
        select(func.count(IngredienteTable.id_ingrediente)).where(
            IngredienteTable.openfoodfacts_id.isnot(None)
        )
    ).one()
    com_nutricao = session.exec(
        select(func.count(IngredienteTable.id_ingrediente)).where(
            IngredienteTable.calorias.isnot(None)
        )
    ).one()

    return {
        "ingredientes": {
            "total": total,
            "com_usda": com_usda,
            "com_openfoodfacts": com_off,
            "com_dados_nutricionais": com_nutricao,
        },
    }
