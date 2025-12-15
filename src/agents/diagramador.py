from agno.agent import Agent
from agno.models.google import Gemini

from src.core.settings import Settings
from src.core.agent_db import get_agent_db


CARROSSEL_TEMPLATE = '''
TEMPLATE DE CARROSSEL CSS PURO (use este modelo - funciona sem JavaScript):

<div class="receita-container">
    <h1>[TÍTULO DA RECEITA]</h1>
    
    <div class="carousel">
        <!-- Radio inputs para controlar slides (hidden) -->
        <input type="radio" name="slide" id="slide1" checked>
        <input type="radio" name="slide" id="slide2">
        <input type="radio" name="slide" id="slide3">
        <!-- Adicione mais inputs conforme necessário -->
        
        <div class="slides">
            <!-- Para cada imagem/passo, criar um slide assim: -->
            <div class="slide">
                <img src="[URL_IMAGEM]" alt="Passo 1">
                <div class="slide-caption"><strong>Passo 1:</strong> [DESCRIÇÃO]</div>
            </div>
            <div class="slide">
                <img src="[URL_IMAGEM]" alt="Passo 2">
                <div class="slide-caption"><strong>Passo 2:</strong> [DESCRIÇÃO]</div>
            </div>
            <!-- Continue para cada passo -->
        </div>
        
        <!-- Labels para navegação (dots) -->
        <div class="nav-dots">
            <label for="slide1" class="dot"></label>
            <label for="slide2" class="dot"></label>
            <label for="slide3" class="dot"></label>
            <!-- Adicione mais labels conforme necessário -->
        </div>
    </div>
    
    <div class="content-section">
        <h2>Ingredientes</h2>
        <ul class="ingredientes-list">
            <li>[quantidade] [unidade] de [ingrediente]</li>
        </ul>
    </div>
    
    <div class="content-section">
        <h2>Modo de Preparo</h2>
        <ol class="passos-list">
            <li><strong>Passo 1:</strong> [descrição]</li>
        </ol>
    </div>
</div>

<style>
.receita-container { font-family: 'Segoe UI', Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #fff; }
.receita-container h1 { text-align: center; color: #2d3748; border-bottom: 3px solid #48bb78; padding-bottom: 15px; margin-bottom: 30px; }
.receita-container h2 { color: #4a5568; border-left: 4px solid #48bb78; padding-left: 15px; margin-top: 30px; }

/* Carousel CSS Puro */
.carousel { position: relative; max-width: 700px; margin: 0 auto 30px; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
.carousel input[type="radio"] { display: none; }
.slides { display: flex; transition: transform 0.5s ease; }
.slide { min-width: 100%; }
.slide img { width: 100%; height: 400px; object-fit: cover; display: block; }
.slide-caption { background: rgba(0,0,0,0.7); color: white; padding: 15px; text-align: center; }

/* Navegação por dots */
.nav-dots { text-align: center; padding: 15px; background: #f7fafc; }
.dot { display: inline-block; width: 14px; height: 14px; margin: 0 6px; background: #cbd5e0; border-radius: 50%; cursor: pointer; transition: all 0.3s; }
.dot:hover { background: #a0aec0; }

/* Controle dos slides via CSS */
#slide1:checked ~ .slides { transform: translateX(0%); }
#slide2:checked ~ .slides { transform: translateX(-100%); }
#slide3:checked ~ .slides { transform: translateX(-200%); }
#slide4:checked ~ .slides { transform: translateX(-300%); }
#slide5:checked ~ .slides { transform: translateX(-400%); }
#slide6:checked ~ .slides { transform: translateX(-500%); }
#slide7:checked ~ .slides { transform: translateX(-600%); }
#slide8:checked ~ .slides { transform: translateX(-700%); }
#slide9:checked ~ .slides { transform: translateX(-800%); }
#slide10:checked ~ .slides { transform: translateX(-900%); }
#slide11:checked ~ .slides { transform: translateX(-1000%); }
#slide12:checked ~ .slides { transform: translateX(-1100%); }

/* Dot ativo */
#slide1:checked ~ .nav-dots label[for="slide1"],
#slide2:checked ~ .nav-dots label[for="slide2"],
#slide3:checked ~ .nav-dots label[for="slide3"],
#slide4:checked ~ .nav-dots label[for="slide4"],
#slide5:checked ~ .nav-dots label[for="slide5"],
#slide6:checked ~ .nav-dots label[for="slide6"],
#slide7:checked ~ .nav-dots label[for="slide7"],
#slide8:checked ~ .nav-dots label[for="slide8"],
#slide9:checked ~ .nav-dots label[for="slide9"],
#slide10:checked ~ .nav-dots label[for="slide10"],
#slide11:checked ~ .nav-dots label[for="slide11"],
#slide12:checked ~ .nav-dots label[for="slide12"] { background: #48bb78; transform: scale(1.2); }

.ingredientes-list, .passos-list { padding-left: 25px; line-height: 1.8; }
.ingredientes-list li, .passos-list li { margin: 10px 0; padding: 5px 0; }
</style>
'''


def create_diagramador_agent(settings: Settings) -> Agent:
    return Agent(
        name="Diagramador",
        model=Gemini(
            id=settings.gemini_model_text,
            api_key=settings.gemini_api_key,
        ),
        debug_mode=True,
        db=get_agent_db(),
        add_history_to_context=True,
        num_history_runs=5,
        description="Agente HTML (Diagramador): monta micro página HTML com carrossel interativo, ingredientes e passos.",
        instructions=[
            "Você é um diagramador especialista em criar páginas HTML de receitas bonitas e funcionais.",
            "",
            "## DADOS QUE VOCÊ RECEBERÁ:",
            "- Nome do produto",
            "- Lista de URLs de imagens (uma para cada passo)",
            "- Lista de ingredientes (com nome, quantidade, unidade)",
            "- Lista de passos do modo de preparo",
            "",
            "## O QUE VOCÊ DEVE GERAR:",
            "Uma página HTML completa com CARROSSEL CSS PURO (sem JavaScript):",
            "1. Título da receita",
            "2. CARROSSEL DE IMAGENS usando inputs radio e labels:",
            "   - Input radio hidden para cada slide (id='slide1', 'slide2', etc)",
            "   - O primeiro input deve ter 'checked'",
            "   - Div .slides contendo os slides",
            "   - Div .nav-dots com labels (for='slide1', etc) como dots clicáveis",
            "   - Legenda com o passo correspondente em cada slide",
            "3. Seção de ingredientes formatada",
            "4. Seção de modo de preparo numerado",
            "",
            "## REGRAS IMPORTANTES:",
            "- Use EXATAMENTE as URLs de imagens fornecidas (começam com /media/)",
            "- NÃO USE JAVASCRIPT - use apenas CSS puro com inputs radio",
            "- Inclua CSS inline no HTML (tag <style>)",
            "- Crie um input radio e um label/dot para CADA imagem/passo",
            "- Retorne APENAS o HTML, sem markdown ou explicações",
            "- Design moderno com cores verdes (#48bb78)",
            "",
            f"## TEMPLATE DE REFERÊNCIA:\n{CARROSSEL_TEMPLATE}",
        ],
    )
