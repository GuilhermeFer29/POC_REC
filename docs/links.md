Notei que o Agno é o novo nome do antigo framework Phidata. Atualizei os links para refletir essa mudança recente, garantindo que você acesse a documentação mais moderna.

📚 Links Oficiais da Stack
FastAPI (Backend API)

🌐 Site Oficial: fastapi.tiangolo.com

🐙 GitHub: github.com/fastapi/fastapi

Contexto: Responsável por expor seus agentes como API e gerenciar os WebSockets para conexões ativas.

SQLModel (ORM / Banco de Dados)

🌐 Site Oficial: sqlmodel.tiangolo.com

🐙 GitHub: github.com/fastapi/sqlmodel

Contexto: Criado pelo mesmo autor do FastAPI, une o Pydantic com SQLAlchemy. Perfeito para gerenciar suas tabelas MySQL de forma validada.

Agno (Antigo Phidata - Framework de Agentes)

🌐 Site Oficial: agno.com

📖 Documentação: docs.agno.com

🐙 GitHub: github.com/agno-agi/agno

Contexto: O "cérebro" da sua operação. É aqui que você criará o Orquestrador, o Chef de Receitas e o Gerador de Imagens. O Agno possui integração nativa com FastAPI.

Qdrant (Banco Vetorial / RAG)

🌐 Site Oficial: qdrant.tech

📖 Documentação Python: python-client.qdrant.tech

Contexto: Armazenará os embeddings dos "Livros de Receita" e "Livros de Fotografia" para o RAG dos seus agentes.

MySQL (Banco de Dados Relacional)

🌐 Site Oficial: mysql.com

📖 Documentação: dev.mysql.com/doc


RAG (Retrieval-Augmented Generation):

- Documentação: https://docs.agno.com/basics/knowledge/agents/overview

- Contexto: Armazenará os usuários, o histórico de pedidos e o HTML final gerado como parte do processo de geração de receitas.

- Uso no Projeto: Será utilizado pelos agentes para buscar informações relevantes de "Livros de Receita" e "Livros de Fotografia" durante a geração do conteúdo.