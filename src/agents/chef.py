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
        debug_mode=True,
        db=get_agent_db(),
        add_history_to_context=True,
        num_history_runs=5,
        description="Agente Receita (Chef): gera json_ingredientes e json_modo_preparo com apoio de RAG/Qdrant.",
        instructions=[
            "Você é um chef especialista em criar receitas.",
            "Receba id_produto, descrição do cliente e referências.",
            "Consulte o contexto de ingredientes e livros de receita (RAG) para selecionar ingredientes.",
            "Gere json_ingredientes (lista de ingredientes com quantidade) e json_modo_preparo (lista de passos ordenados).",
            "Valide via Pydantic que os JSONs estão bem formados.",
            "Retorne ao Orquestrador para atualizar status e emitir eventos WebSocket.",
        ],
    )
