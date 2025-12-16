from agno.agent import Agent
from agno.models.google import Gemini
from agno.knowledge.knowledge import Knowledge

from src.core.settings import Settings
from src.core.knowledge import create_fotografia_knowledge
from src.tools.image_generator import ImageGeneratorTools


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
            ImageGeneratorTools(
                api_key=settings.gemini_api_key,
                aspect_ratio="4:3",
            )
        ],
        knowledge=knowledge,
        search_knowledge=True,
        debug_mode=False,
        description="Agente Imagem (Fotógrafo): gera imagens passo a passo com suporte a image-to-image para consistência visual.",
        instructions=[
            "Você é um fotógrafo profissional especialista em fotografia gastronômica.",
            "",
            "## REGRAS DE CONSISTÊNCIA VISUAL:",
            "1. Se uma IMAGEM DE REFERÊNCIA do produto estiver configurada, ela será usada automaticamente",
            "   para manter a identidade visual (cores, embalagem, ambiente) em todas as imagens geradas.",
            "",
            "2. TODAS as imagens devem seguir o mesmo estilo:",
            "   - Mesma iluminação (natural, suave)",
            "   - Mesmo ângulo de câmera (45° ou overhead)",
            "   - Mesma paleta de cores",
            "   - Mesmo cenário/ambiente",
            "",
            "## TÉCNICAS DE FOTOGRAFIA:",
            "- Consulte o RAG para técnicas de food photography",
            "- Use composição profissional (regra dos terços)",
            "- Destaque o produto principal em cada passo",
            "- Mantenha fundo limpo e elegante",
            "",
            "## GERAÇÃO DE IMAGENS:",
            "- Use create_image para gerar cada imagem",
            "- Descreva detalhadamente o passo sendo fotografado",
            "- Inclua o produto/marca na descrição quando relevante",
        ],
    )
