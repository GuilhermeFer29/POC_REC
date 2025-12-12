# POC Gerador de Receitas — Plano Faseado (FastAPI, SqlModel, Agno, Qdrant, MySQL)

## 0. Contexto e Premissas
- Objetivo: POC que recebe descrição de produto do cliente (`id_produto`) e produz receita estruturada (JSON), imagens passo a passo e micro página HTML, persistindo tudo em MySQL e vetores em Qdrant, com opção de publicar no WordPress.
- Stack: FastAPI + WebSocket, SqlModel (MySQL), Agno (orquestração de agentes), Qdrant (RAG), Gemini (text/embeddings), modelo de imagem “Nano Banana”, Celery/Redis (tarefas pesadas), WordPress (publicação), Streamlit/Gradio (demonstração).
- Referências oficiais (docs/links.md): FastAPI, SqlModel, Agno, Qdrant, MySQL, RAG (Agno knowledge agents), WordPress REST API.

## 1. Princípios e Boas Práticas
- Configuração: `.env` + `pydantic-settings`; nunca commitar segredos; separar dev/prod; incluir chaves Gemini, DSN MySQL, Redis, Qdrant e credenciais WP (application password/JWT).
- Observabilidade: logs estruturados (JSON) com correlation-id (`id_receita`); métricas por etapa (recipe/images/html/WP); tracing opcional.
- Resiliência: timeouts e retries para LLM/imagem/WP; circuit breaker simples; fila Celery para jobs longos; idempotência por `id_receita` + passo.
- Segurança: tokens de API/JWT simples; rate limit; CORS restrito; sanitizar HTML salvo e enviado ao WP; proteger credenciais WP.
- Dados: migrações (SqlModel/SQLAlchemy); índices em FKs; versionar prompts, seeds e versões de HTML; guardar referências de publicação WP.
- Testes: unit para prompts/parsers; integração com stubs (Gemini/imagem/WP); contrato de endpoints; smoke e2e com workflow completo.

## 2. Fases de Entrega
### Fase 1 — Fundação de Infra (Backend básico)
- Subir FastAPI com healthcheck e `/version`.
- Conexão MySQL via SqlModel; criar base de migrações.
- Cliente Qdrant inicial + criação de collection (ex.: `receitas`) com dimensão conforme embeddings Gemini.
- Estrutura de config (`settings.py`), logging estruturado, middlewares de request-id.
- Definir modelos SqlModel (rascunho) conforme BD: `produtos_cliente`, `ingredientes`, `receitas` (+ extensões auxiliares `imagens`, `vectors`, `tasks`).
- Entregáveis: API rodando local, migrations aplicáveis, collection criada.

### Fase 2 — Contratos de API e Esquemas
- Definir endpoints REST: `POST /receitas`, `GET /receitas/{id}`, WebSocket `/receitas/{id}/stream` (esqueleto); `GET /produtos`, `GET /produtos/{id}`, `GET /ingredientes`.
- Schemas Pydantic: entrada (id_produto, descricao_produto/cliente, refs/imagens), saída (status, json_ingredientes, json_modo_preparo, imagens, content_html, link/id WP).
- Estados de workflow: `pending`, `generating_recipe`, `generating_images`, `generating_html`, `done`, `error`.
- Entregáveis: OpenAPI servindo; contratos revisados.

### Fase 3 — Orquestrador (Agno) 
- Responsabilidade (conforme descrição): ao receber a solicitação (via agendador/API), buscar no MySQL o produto (`produtos_cliente`) e insumos necessários; acionar o Agente Receita (Chef) para gerar `json_ingredientes` e `json_modo_preparo` (com apoio de RAG/Qdrant); ao receber o resultado, enviar ao Agente Imagem para gerar imagens do modo de preparo; por fim, entregar ao Agente HTML para montar o `content_html`.
- Persistir `tasks`/status a cada etapa; publicar eventos no WebSocket (`pending` → `generating_recipe` → `generating_images` → `generating_html` → `done`/`error`).
- Inputs mínimos: `id_produto`, descrição opcional do cliente, referências de imagem (produto/ingredientes), parâmetros de geração.
- Saídas: `id_receita`, `status`, `json_ingredientes`, `json_modo_preparo`, links de imagens por passo, `content_html` (ou id da página WP se publicado).
- Entregáveis: fluxo end-to-end com stubs (sem chamadas externas), armazenando estados no DB e registrando vetores no Qdrant quando aplicável.

### Fase 4 — RAG Base (Qdrant + Gemini Embeddings)
- Ingestão: criar embeddings de fontes de “livros de receita” e “livros de fotografia” (estética) para apoiar Chef e Fotógrafo. Dados podem ser dataset de exemplo no POC.
- Indexação: Qdrant com payload incluindo `tipo` (ingrediente|passo|foto_ref|produto_ref), `id_produto` (quando houver vínculo), e contexto do tópico/receita.
- Consulta: função de busca semântica reutilizável pelos agentes Receita (para ingredientes/método) e Imagem (para referências estéticas e consistência visual).
- Entregáveis: coleção populada e consultas retornando contexto relevante para ingredientes, modo de preparo e referências visuais.

### Fase 5 — Agente Receita (Chef)
- Objetivo: Receber do Orquestrador o `id_produto`, descrição do cliente e refs; consultar MySQL (`produtos_cliente`, `ingredientes`) e RAG (Qdrant + “livros de receita”) para selecionar ingredientes e contexto.
- Geração: Prompt RAG + Gemini produz `json_ingredientes` e `json_modo_preparo` completos; validar via Pydantic.
- Persistência: salvar em `receitas` (campos json_ingredientes, json_modo_preparo, status) e opcionalmente registrar vetores dos passos/ingredientes em Qdrant.
- Comunicação: retornar ao Orquestrador, atualizar status (`generating_recipe` → `generating_images`), emitir eventos WebSocket.
- Entregáveis: receita real gerada com RAG + persistência consistente no DB.

### Fase 6 — Agente Imagem (Fotógrafo)
- Objetivo: Receber do Orquestrador o `json_modo_preparo` (passos), refs de imagem (produto + ingredientes + identidade do cliente) e gerar um passo a passo ilustrado, garantindo consistência do produto em todas as etapas.
- Geração: usar modelo de imagem “Nano Banana” (Gemini) por passo (ou stub configurável); prompts incluem texto do passo, produto, identidade visual e imagens de ingredientes. Considerar RAG com “livros de fotografia” para estética/composição.
- Persistência: salvar arquivos de imagem em pasta/obj storage (ex.: `media/receitas/{id_receita}/step_{step_index}.png`), registrar seeds/params e, quando for publicar no WP, fazer upload de cada imagem para `/wp-json/wp/v2/media` e armazenar o `source_url` retornado no DB (tabela `images`). Status: `generating_images` → `generating_html`.
- Comunicação: devolver links ao Orquestrador (priorizar `source_url` do WP quando disponível); permitir reprocessar passo isolado. Emitir eventos WebSocket.
- Entregáveis: sequência de imagens ordenadas por passo, prontas para o Agente HTML; dados persistidos no DB.

### Fase 7 — Agente HTML (Diagramador)
- Objetivo: Receber do Orquestrador as imagens geradas (ordenadas por passo), os textos de ingredientes (`json_ingredientes`) e o modo de preparo (`json_modo_preparo`) e montar uma micro página.
- Composição: carrossel de imagens do passo a passo, seção de ingredientes ordenados, seção de modo de preparo ordenado, destaque para a imagem do produto do cliente.
- Sanitização e persistência: sanitizar HTML, salvar em `html_pages` (hash/version) e manter `content_html` em `receitas`; status `generating_html` → `done`.
- Publicação: opcionalmente publicar no WordPress (Fase 10). Se as imagens forem subidas ao WP, usar os `source_url` das mídias no HTML; armazenar o id/link retornado do post.
- Entregáveis: HTML final servível e persistido; endpoint para recuperar/visualizar ou publicar no WP com suporte a reenvio, atualização, histórico e versionamento; API para gerenciar versões e revisões.

### Fase 8 — Assíncrono e Robustez
- Mover tarefas pesadas para Celery + Redis: geração de imagens (passo a passo) e publicação HTML/WordPress.
- Garantir idempotência: chave por `id_receita` + `step_index`; permitir reprocessar passo ou republish WP.
- Retries com backoff para chamadas a LLM/imagem/WP; DLQ opcional; timeouts e circuit breaker simples.
- Entregáveis: workers rodando; tasks não bloqueiam o request inicial; reprocessamento seguro e registrando status em `tasks`.

### Fase 9 — Observabilidade e Qualidade
- Métricas (prometheus/OTel): tempo por etapa (`generating_recipe`, `generating_images`, `generating_html`, publicação WP), custo aproximado LLM/imagem, falhas por agente.
- Logs estruturados com correlation-id (`id_receita`), incluindo prompts resumidos e seeds de imagem (sem vazar segredos).
- Testes: unit (prompts/parsers), integração com stubs de Gemini/imaginação/WP, contrato (OpenAPI), smoke e2e do workflow completo.

### Fase 10 — Publicação WordPress (Frontend de Demonstração)
- Publicar HTML final no WordPress via REST API oficial (`/wp-json/wp/v2/posts` ou página custom), com auth por Application Password ou JWT (conforme doc WP).
- Payload: `title`, `content` (HTML gerado), `status=publish` (ou `draft` para revisão); opcional `meta`/`custom fields` para ids de receita e produto.
- Sanitizar/escapar antes de enviar; manter cópia no MySQL (`content_html`) como fonte de verdade.
- Opcional: gerar página e embutir assets (imagens) já hospedadas; considerar `featured_media` para imagem principal.
- Entregáveis: publicação automática funcionando; endpoint/admin para reenviar/atualizar post WP; demo simples (pode usar Streamlit/Gradio apenas para acionar e visualizar link WP).

## 3. Modelagem de Dados (rascunho SqlModel)
**Modelo solicitado (MySQL - BD):**
- **produtos_cliente**: id_produto, nome_produto, tipo_produto, imagem_produto, descricao.
- **ingredientes**: id_ingrediente, nome_singular, nome_plural, tipo_ingrediente, imagem_ingrediente, descricao.
- **receitas**: id_receita, json_ingredientes, json_modo_preparo, content_html, status.

**Extensões sugeridas para o POC:**
- `receitas`: adicionar `id_produto` (FK para produtos_cliente), `created_at`, `updated_at` para rastreabilidade.
- `imagens` (nova): id, id_receita (FK), step_index, url, prompt_meta, seed, created_at.
- `vectors` (nova): id, id_receita (FK), kind (ingrediente|step|image_ref), qdrant_id, payload.
- `tasks` (nova): id, id_receita (FK), type (recipe|image|html), status, error, created_at, updated_at.

## 4. Endpoints Propostos (referência)
- `POST /receitas`: cria pedido associado a um produto (id_produto) e descrição; retorna id_receita + status inicial.
- `GET /receitas/{id}`: status e payload agregado (json_ingredientes, json_modo_preparo, imagens por passo, content_html, id_produto).
- `WS /receitas/{id}/stream`: eventos de progresso.
- `GET /produtos`: lista produtos_cliente (para seleção de contexto).
- `GET /produtos/{id}`: detalhes do produto (nome, tipo, imagem).
- `GET /ingredientes`: lista catálogo de ingredientes (opcional, apoio a UI/admin).
- Admin/ops (opcionais): regenerar imagens de um passo; regerar HTML; listar tasks; reindexar vetor de um produto/receita.

## 5. Integrações e Config
- Gemini: chave via env; timeouts + retries; modo embeddings + text.
- Qdrant: coleção `receitas`; definir dimensão conforme embedding Gemini; payload com `tipo` e `recipe_id`/`id_produto`.
- MySQL: DSN via env; charset utf8mb4; migrations antes de subir API.
- Redis/Celery: fila para imagens/HTML e publicação WP; result backend opcional.
- Storage de imagens: pasta/obj storage acessível pela API; path determinístico `media/receitas/{id_receita}/step_{i}.png`; DB guarda path/URL local, `source_url` do WP (quando fizer upload) e metadados.
- WordPress: REST API (`/wp-json/wp/v2/posts`), auth via Application Password ou JWT; requer URL base e credenciais no env.
- Agno: definir agentes (orquestrador, chef, fotógrafo, diagramador) com toolset (DB, Qdrant, HTTP fetch opcional para web search controlada).

## 6. Checklist de Prontidão por Fase
- F1: healthcheck OK, migrations aplicam, collection Qdrant criada.
- F2: OpenAPI exposta, contratos revisados (endpoints /receitas, /produtos, /ingredientes, WS).
- F3: fluxo stub end-to-end salva estados.
- F4: RAG responde consultas coerentes (ingredientes e referências visuais).
- F5: JSON de receita válido e persistido.
- F6: imagens por passo persistidas com seeds/params.
- F7: HTML salvo, versionado e recuperável; pronto para publicar.
- F8: tarefas pesadas assíncronas e resilientes (imagens/HTML/WP).
- F9: métricas expostas, testes mínimos verdes.
- F10: demo funcional, publicação WP funcionando (publish/update/retry).

## 7. Próximos Passos Imediatos
1) Criar `.env.example` com chaves (Gemini), DSN MySQL, Redis, Qdrant host/port, credenciais WP.
2) Implementar Fase 1 (infra) e Fase 2 (contratos) para destravar integração e testes.
3) Definir dimensão de embedding (Gemini) e criar collection Qdrant; ajustar payload schema.
4) Especificar dataset inicial de RAG (receitas + fotografia) e pipeline de ingestão; validar busca semântica.
5) Definir payload de publicação WP (campos obrigatórios/opcionais) e rota de reenvio/atualização.

