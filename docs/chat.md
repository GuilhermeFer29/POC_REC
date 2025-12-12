Aqui está a estrutura do seu sistema organizada pelos papéis definidos:

1. Arquitetura e Stack Tecnológica
A base técnica do projeto permanece consistente com o PDF anterior, mas com definições mais claras:


Orquestração: LangChain é a escolha sugerida para garantir controle, embora o Agno tenha sido considerado.


LLM & RAG: Google Gemini via API com Qdrant para embeddings.



Banco de Dados: MySQL  para dados estruturados e HTML final.


Infraestrutura: FastAPI/Websocket para manter a conexão ativa e Celery/Redis para filas e cache.



Modelo de Imagem: "Nano Banana" é especificado como o modelo gerador.

2. O Fluxo dos Agentes (Workflow)
Abaixo, detalho a responsabilidade de cada agente conforme descrito no arquivo:

🤖 1. Agente Orquestrador (O Gerente)
Este é o ponto central. Ele não produz conteúdo, mas garante que a linha de montagem funcione.


Gatilho: Recebe a solicitação de um "Agendador".


Função: Busca os dados iniciais no banco, chama o Agente de Receita, pega o resultado (JSON), passa para o Agente de Imagem e, finalmente, para o Agente de HTML.

🧠 2. Agente Gerador de Receita (O Chef)
Focado puramente em texto e dados estruturados.


Entrada: Descrição do produto do cliente.

Processamento:

Pesquisa na Web e RAG (baseado em livros de receita).

Seleciona ingredientes que combinem com o produto do cliente.


Saída: Um JSON Organizado contendo ingredientes e modo de preparo, salvo no banco.

🎨 3. Agente Gerador de Imagem do Modo de Preparo (O Fotógrafo)
Este é o agente mais complexo visualmente, pois exige consistência (manter a identidade do produto).


Entrada: O "modo de preparo" (texto) vindo do Orquestrador e as imagens de referência (produto do cliente + ingredientes).

Diferencial Técnico:

O objetivo não é criar imagens genéricas, mas um passo a passo onde o produto do cliente aparece sendo utilizado.

Utiliza RAG focado em "Livros de Fotografia" para melhorar a estética.


Modelo: Utiliza o "Nano Banana".


Saída: Links das imagens geradas salvos no banco.

📝 4. Agente Gerador de HTML (O Diagramador)
Responsável pela montagem final para o frontend.


Entrada: Recebe tudo que foi gerado anteriormente (Imagens, Texto de Ingredientes, Modo de Preparo).

Processamento: Cria uma "micro página" contendo:

Carrossel de imagens do passo a passo.

Seção de ingredientes ordenados.

Seção de modo de preparo ordenado.

Destaque para a imagem do produto do cliente.


Saída: Código HTML pronto salvo no banco de dados.



Com base no arquivo POC_Receitas.pdf que você enviou, o conteúdo é um esboço técnico (Proof of Concept - POC) para um sistema gerador de receitas culinárias utilizando Inteligência Artificial.

Aqui está o conteúdo organizado e estruturado por categorias técnicas, conforme solicitado:

1. Stack Tecnológica Sugerida
O documento lista explicitamente as ferramentas e tecnologias para o backend, dados e IA:

Backend & Conectividade:

FastAPI: Para a criação da API .

Websocket: Para manter conexões ativas (provavelmente para streaming da resposta da IA) .

Banco de Dados & Cache:

MySQL: Banco de dados relacional principal .

Celery/Redis: Sugerido para persistência de cache e gerenciamento de filas de tarefas .

IA & RAG (Retrieval-Augmented Generation):

Qdrant: Banco de dados vetorial para embeddings .

Google API: Fonte dos embeddings e do modelo de linguagem (LLM) .

Google Gemini: A API de IA escolhida para o projeto .

Orquestração de Agentes:

LangChain: Sugerido como a escolha principal para ter maior controle sobre o fluxo .

Agno: Mencionado como uma opção alternativa, mas preterida em favor do LangChain neste esboço .

Frontend (Para Testes):

Streamlit ou Gradio: Sugeridos para prototipagem rápida da interface .

2. Fluxo Lógico do Processo
O diagrama descreve um fluxo de 3 passos principais para a geração do conteúdo:

Geração do Texto: Criar a receita em formato de texto .

Geração de Imagem Contextual: Gerar imagens do passo a passo, utilizando como referência a imagem de um "produto de marca" (para garantir que o produto do cliente apareça na imagem gerada pela IA) .

Montagem e Persistência: Montar o HTML final e gravar no banco de dados .

3. Arquitetura de Agentes (Interpretado do Diagrama)
Embora algumas partes do texto no diagrama estejam difíceis de ler, é possível identificar uma estrutura de múltiplos agentes orquestrados:

Agente Orquestrador: O nó central que recebe o pedido e distribui as tarefas .

Agente Gerador de Receita: Responsável por criar o texto e lista de ingredientes, consultando o banco de dados .

Agente Gerador de Imagem (do modo de preparo): Responsável por criar as instruções visuais .

Agente Gerador de HTML: Consolida o texto e as imagens em um formato web para salvar no banco .

Observação sobre o seu perfil: Notei que o documento menciona a escolha entre Agno e LangChain. Como você tem interesse recente no framework Agno (mencionado em nossas conversas passadas), esta arquitetura poderia ser adaptada para usar o Agno em vez do LangChain, caso prefira testar esse novo framework.

Gostaria que eu montasse uma estrutura de código em Python (usando LangChain ou Agno) para o "Agente Orquestrador" descrito nesse diagrama?