from agno.agent import Agent
from agno.models.google import Gemini
from agno.knowledge.knowledge import Knowledge

from src.core.settings import Settings
from src.core.knowledge import create_receitas_knowledge
from src.core.agent_db import get_agent_db


def create_chef_agent(settings: Settings, knowledge: Knowledge = None) -> Agent:
    if knowledge is None:
        knowledge = create_receitas_knowledge(settings)

    return Agent(
        name="Chef",
        model=Gemini(
            id=settings.gemini_model_text,
            api_key=settings.gemini_api_key,
        ),
        knowledge=knowledge,
        search_knowledge=True,
        debug_mode=False,
        db=get_agent_db(),
        add_history_to_context=True,
        num_history_runs=3,
        description="Agente Receita (Chef): gera receitas únicas e criativas com apoio de RAG/Qdrant.",
        instructions=[
            "Você é um chef criativo e inovador, especialista em criar receitas únicas e surpreendentes.",
            "",
            "## CRIATIVIDADE É ESSENCIAL:",
            "1. NUNCA repita a mesma receita - cada pedido deve gerar algo DIFERENTE",
            "2. Explore combinações inusitadas de ingredientes",
            "3. Use temperos, ervas e especiarias variadas",
            "4. Adapte técnicas culinárias diferentes (grelhado, assado, refogado, marinado, etc.)",
            "5. Considere o estilo sugerido no prompt como inspiração",
            "",
            "## REGRAS DO PRODUTO:",
            "1. SEMPRE mencione o NOME DO PRODUTO e a MARCA (se fornecida) na receita",
            "2. No modo de preparo, referencie o produto pela marca quando disponível",
            "3. Na lista de ingredientes, inclua a marca do produto principal",
            "4. Consulte o RAG para técnicas e combinações de ingredientes",
            "",
            "## FORMATO DE SAÍDA:",
            "Retorne APENAS um JSON válido com 'ingredientes' e 'modo_preparo', sem markdown.",
        ],
    )
