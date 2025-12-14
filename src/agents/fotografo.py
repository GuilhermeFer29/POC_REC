from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.nano_banana import NanoBananaTools
from agno.knowledge.knowledge import Knowledge

from src.core.settings import Settings
from src.core.knowledge import create_fotografia_knowledge


def create_fotografo_agent(settings: Settings, knowledge: Knowledge = None) -> Agent:
    if knowledge is None:
        knowledge = create_fotografia_knowledge(settings)

    return Agent(
        name="Fotografo",
        model=Gemini(
            id=settings.gemini_model_text,
            api_key=settings.gemini_api_key,
        ),
        tools=[
            NanoBananaTools(
                api_key=settings.gemini_api_key,
                aspect_ratio="4:3",
            )
        ],
        knowledge=knowledge,
        search_knowledge=True,
        description="Agente Imagem (Fotógrafo): gera imagens passo a passo com Nano Banana, garantindo consistência visual.",
        instructions=[
            "Você é um fotógrafo especialista em fotografia de alimentos.",
            "Receba json_modo_preparo (passos), refs de imagem (produto + ingredientes + identidade do cliente).",
            "Use a função create_image para gerar uma imagem para cada passo.",
            "Consulte RAG com livros de fotografia para estética/composição.",
            "Mantenha consistência do produto em todas as etapas.",
            "Salve imagens em media/receitas/{id_receita}/step_{step_index}.png.",
            "Registre seeds/params para reprodutibilidade.",
            "Permita reprocessar passo isolado se necessário.",
            "Emita eventos WebSocket ao concluir cada passo.",
        ],
    )
