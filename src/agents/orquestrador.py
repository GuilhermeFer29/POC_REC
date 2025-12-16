import json
import logging
import time
from pathlib import Path
from typing import Optional
from uuid import uuid4

from sqlmodel import Session

from src.core.settings import Settings
from src.core.knowledge import create_receitas_knowledge, create_fotografia_knowledge
from src.agents.chef import create_chef_agent
from src.agents.fotografo import create_fotografo_agent
from src.agents.diagramador import create_diagramador_agent
from src.service.receitas_service import atualizar_status, obter_receita
from src.models.receitas import ReceitaTable
from src.models.produtos import ProdutoClienteTable
from src.tools.image_generator import set_reference_image

logger = logging.getLogger(__name__)


class Orquestrador:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.receitas_kb = create_receitas_knowledge(settings)
        self.fotografia_kb = create_fotografia_knowledge(settings)
        self.chef = create_chef_agent(settings, knowledge=self.receitas_kb)
        self.fotografo = create_fotografo_agent(settings, knowledge=self.fotografia_kb)
        self.diagramador = create_diagramador_agent(settings)

    def _montar_dados_produto(self, produto: ProdutoClienteTable) -> dict:
        """Monta os dados do produto de forma padronizada para todos os agentes."""
        nome_completo = produto.nome_produto
        if produto.marca:
            nome_completo = f"{produto.nome_produto} {produto.marca}"
        
        imagem_url = ""
        if produto.imagem_produto:
            imagem_url = f"/{produto.imagem_produto}"
        
        return {
            "nome": produto.nome_produto,
            "marca": produto.marca or "",
            "nome_completo": nome_completo,
            "tipo": produto.tipo_produto or "",
            "descricao": produto.descricao or "",
            "imagem_url": imagem_url,
            "tem_imagem": bool(produto.imagem_produto),
        }

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

        shared_session_id = f"receita_{receita_id}_{uuid4().hex[:8]}"
        dados_produto = self._montar_dados_produto(produto)
        
        logger.info(f"[Receita {receita_id}] Iniciando: {dados_produto['nome_completo']}")

        try:
            # ETAPA 1: Chef gera receita
            atualizar_status(session, receita_id, "generating_recipe")
            resultado_chef = self._gerar_receita(dados_produto, descricao_cliente, shared_session_id)
            self._salvar_receita(session, receita, resultado_chef)
            logger.info(f"[Receita {receita_id}] Chef: {len(resultado_chef.get('modo_preparo', []))} passos")

            # ETAPA 2: Fotógrafo gera imagens
            atualizar_status(session, receita_id, "generating_images")
            imagens = self._gerar_imagens(
                receita_id, resultado_chef.get("modo_preparo", []), dados_produto, shared_session_id
            )
            logger.info(f"[Receita {receita_id}] Fotógrafo: {len(imagens)} imagens")

            # ETAPA 3: Diagramador gera HTML
            atualizar_status(session, receita_id, "generating_html")
            html = self._gerar_html(dados_produto, resultado_chef, imagens, shared_session_id)
            self._salvar_html(session, receita, html)

            atualizar_status(session, receita_id, "done")
            logger.info(f"[Receita {receita_id}] Concluída!")
            return {"status": "done", "receita_id": receita_id}

        except Exception as e:
            logger.error(f"[Receita {receita_id}] Erro: {e}")
            atualizar_status(session, receita_id, "error")
            return {"status": "error", "receita_id": receita_id, "error": str(e)}

    def _gerar_receita(self, dados_produto: dict, descricao_cliente: Optional[str], session_id: str) -> dict:
        """
        Chama o agente Chef para gerar a receita.
        
        Placeholders passados ao Chef:
        - {nome_completo}: Nome do produto + marca (ex: "Leite Condensado Moça")
        - {nome}: Nome do produto (ex: "Leite Condensado")
        - {marca}: Marca do produto (ex: "Moça")
        - {tipo}: Tipo do produto (ex: "Laticínio")
        - {descricao}: Descrição do produto ou do cliente
        """
        # Gerar variação aleatória para receitas diferentes
        import random
        estilos = [
            "clássica tradicional brasileira",
            "gourmet sofisticada",
            "rápida e prática do dia a dia",
            "fitness e saudável",
            "comfort food aconchegante",
            "internacional com toque brasileiro",
            "para ocasiões especiais",
            "econômica e rendosa",
        ]
        tecnicas = [
            "grelhado", "assado no forno", "refogado", "cozido lentamente",
            "selado na frigideira", "marinado", "defumado", "ao molho",
            "empanado", "na pressão", "na churrasqueira", "sous vide",
        ]
        acompanhamentos = [
            "arroz e farofa", "purê de batatas", "salada fresca", "legumes assados",
            "massa", "risoto", "polenta", "batatas rústicas", "vinagrete",
        ]
        
        estilo = random.choice(estilos)
        tecnica = random.choice(tecnicas)
        acompanhamento = random.choice(acompanhamentos)
        
        prompt = f"""Crie uma receita ÚNICA e CRIATIVA para o produto: {dados_produto['nome_completo']}.

DADOS DO PRODUTO:
- Nome: {dados_produto['nome']}
- Marca: {dados_produto['marca'] or 'Não especificada'}
- Tipo: {dados_produto['tipo'] or 'Não especificado'}
- Descrição: {dados_produto['descricao'] or descricao_cliente or 'Não especificada'}

ESTILO DA RECEITA (use como inspiração):
- Estilo: {estilo}
- Técnica sugerida: {tecnica}
- Acompanhamento sugerido: {acompanhamento}

IMPORTANTE - SEJA CRIATIVO:
- NÃO repita receitas comuns ou óbvias
- Use ingredientes variados e combinações interessantes
- Explore temperos e ervas diferentes
- Crie um nome criativo para a receita se desejar

REGRAS OBRIGATÓRIAS:
1. SEMPRE use o nome completo "{dados_produto['nome_completo']}" ao mencionar o produto principal
2. Na lista de ingredientes, o produto principal deve aparecer como "{dados_produto['nome_completo']}"
3. No modo de preparo, referencie sempre como "{dados_produto['nome_completo']}"

FORMATO DE SAÍDA (JSON):
{{
  "ingredientes": [
    {{"nome": "ingrediente", "quantidade": "X", "unidade": "unidade"}}
  ],
  "modo_preparo": [
    "Passo 1: descrição...",
    "Passo 2: descrição..."
  ]
}}

Retorne APENAS o JSON, sem markdown ou explicações."""

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
        dados_produto: dict,
        session_id: str = None,
    ) -> list:
        """
        Gera imagens para cada passo usando o agente Fotógrafo.
        Se o produto tem imagem cadastrada, configura como referência visual para image-to-image.
        """
        imagens = []
        media_dir = Path(f"media/receitas/{receita_id}")
        media_dir.mkdir(parents=True, exist_ok=True)

        # NÃO usar imagem de referência para evitar colagens/sobreposições
        # A imagem original do produto aparecerá no primeiro slide do carrossel HTML
        set_reference_image(None)

        total_passos = len(passos)
        for i, passo in enumerate(passos):
            passo_num = i + 1
            
            # Prompt para o agente Fotógrafo
            prompt = f"""Gere uma fotografia gastronômica profissional para o passo {passo_num} de {total_passos}:

PASSO: {passo}

PRODUTO: {dados_produto['nome_completo']}

REGRAS OBRIGATÓRIAS:
- NÃO mostre embalagens, rótulos ou etiquetas - mostre APENAS o alimento sendo preparado
- NÃO faça colagem ou sobreposição de imagens
- Fotografia realista do processo de preparo
- Iluminação natural e suave
- Ângulo de 45 graus ou overhead
- Fundo neutro e elegante (tábua de madeira, mármore ou bancada)
- Mantenha consistência visual entre todas as imagens"""

            image_path = f"media/receitas/{receita_id}/step_{i}.png"
            
            # Tentar gerar imagem com retries
            max_retries = 3
            response = None
            for attempt in range(max_retries):
                try:
                    response = self.fotografo.run(prompt, session_id=session_id)
                    break
                except Exception as e:
                    logger.warning(f"[Imagem {passo_num}] Tentativa {attempt+1} falhou: {e}")
                    if attempt < max_retries - 1:
                        time.sleep((attempt + 1) * 3)
            
            # Salvar imagem no disco se foi gerada
            if response and hasattr(response, 'images') and response.images:
                for img in response.images:
                    if hasattr(img, 'content') and img.content:
                        with open(image_path, 'wb') as f:
                            f.write(img.content)
                        break
            
            imagens.append({
                "step_index": i,
                "passo_num": passo_num,
                "passo_descricao": passo,
                "url": image_path,
            })
        
        # Limpar referência após terminar
        set_reference_image(None)
        return imagens

    def _gerar_html(self, dados_produto: dict, resultado_chef: dict, imagens: list, session_id: str = None) -> str:
        """
        Chama o agente Diagramador para gerar o HTML da receita.
        
        Placeholders passados ao Diagramador:
        - {nome_completo}: Nome do produto + marca
        - {nome}: Nome do produto
        - {marca}: Marca do produto
        - {imagem_url}: URL da imagem do produto (primeiro slide)
        - {tem_imagem}: Se o produto tem imagem cadastrada
        - {imagens_passos}: Lista de URLs das imagens dos passos
        - {ingredientes}: Lista de ingredientes com quantidade e unidade
        - {passos}: Lista de passos do modo de preparo
        """
        ingredientes = resultado_chef.get("ingredientes", [])
        passos = resultado_chef.get("modo_preparo", [])
        
        # Montar lista de imagens dos passos com URLs (conversão base64 feita pelo frontend)
        imagens_passos = []
        for img in imagens:
            img_url = f"/{img.get('url', '')}"
            imagens_passos.append({
                "url": img_url,
                "passo_num": img.get('passo_num', img.get('step_index', 0) + 1),
                "descricao": img.get('passo_descricao', passos[img.get('step_index', 0)] if img.get('step_index', 0) < len(passos) else ''),
            })

        # Montar prompt estruturado para o Diagramador
        prompt = f"""Gere uma página HTML completa para a receita com os seguintes dados:

═══════════════════════════════════════════════════════════════
DADOS DO PRODUTO
═══════════════════════════════════════════════════════════════
Nome Completo: {dados_produto['nome_completo']}
Nome: {dados_produto['nome']}
Marca: {dados_produto['marca'] or 'Não especificada'}
Tipo: {dados_produto['tipo'] or 'Não especificado'}

═══════════════════════════════════════════════════════════════
IMAGENS PARA O CARROSSEL
═══════════════════════════════════════════════════════════════
SLIDE 1 (IMAGEM DO PRODUTO - OBRIGATÓRIO SE DISPONÍVEL):
URL: {dados_produto['imagem_url'] if dados_produto['tem_imagem'] else 'NÃO DISPONÍVEL'}
Legenda: "Produto: {dados_produto['nome_completo']}"

SLIDES DOS PASSOS (em ordem):
{json.dumps(imagens_passos, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════
INGREDIENTES
═══════════════════════════════════════════════════════════════
{json.dumps(ingredientes, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════
MODO DE PREPARO
═══════════════════════════════════════════════════════════════
{json.dumps(passos, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════
INSTRUÇÕES DE GERAÇÃO
═══════════════════════════════════════════════════════════════
1. TÍTULO: "Receita de {dados_produto['nome_completo']}"
2. CARROSSEL:
   - Se tem imagem do produto ({dados_produto['tem_imagem']}), ela é o PRIMEIRO slide
   - Cada passo tem sua imagem como slide seguinte
   - Use CSS puro (inputs radio + labels) - SEM JavaScript
3. INGREDIENTES: Lista formatada com quantidade e unidade
4. MODO DE PREPARO: Lista numerada com os passos
5. DESIGN: Moderno, cores verdes (#48bb78), responsivo

Retorne APENAS o HTML completo, sem markdown ou explicações."""

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
