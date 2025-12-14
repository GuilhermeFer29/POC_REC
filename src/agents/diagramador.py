from agno.agent import Agent
from agno.models.google import Gemini

from src.core.settings import Settings


def create_diagramador_agent(settings: Settings) -> Agent:
    return Agent(
        name="Diagramador",
        model=Gemini(
            id=settings.gemini_model_text,
            api_key=settings.gemini_api_key,
        ),
        description="Agente HTML (Diagramador): monta micro página HTML com carrossel, ingredientes e passos.",
        instructions=[
            "Você é um diagramador especialista em criar páginas HTML de receitas.",
            "Receba imagens ordenadas por passo, json_ingredientes e json_modo_preparo.",
            "Monte micro página HTML com carrossel de imagens do passo a passo.",
            "Inclua seção de ingredientes ordenados e seção de modo de preparo ordenado.",
            "Destaque a imagem do produto do cliente.",
            "Sanitize o HTML gerado antes de retornar.",
            "Salve em html_pages (hash/version) e mantenha content_html em receitas.",
            "Opcionalmente publique no WordPress usando source_url das mídias.",
            "Suporte reenvio, atualização, histórico e versionamento.",
        ],
    )
