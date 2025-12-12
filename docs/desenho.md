Tecnologias e Frameworks sugeridos para esse poc By Gui:  FastAPi/Websocket => Manter conexoes ativas
qdrant/embenddigs via API google => Para Rag  
Celery/Redis => persistencia de Cache ?  
DATABSE  => Mysql
Temos a Opção de Agno mas Sugiro o LangChain para ter controle acredito eu.  
API Utilizadas serao do Google Gemini. 
Front-end para testes sugiro Streamlit ou Gradio .

Front-end :  Blog de receita - WP







Agente Gerador de Receita Objetivo => Recebe do Orquestrador a solicitação do cliente e os dados necessários como a descrição de produto do cliente e seleciona do banco os ingredientes baseado em pesquisa via web e RAG(livros de receita). E gera uma receita completa  com os Ingredientes utilizados e  modo de preparo e devolve ao Orquestrador e salva no Banco de Dados como Json Organizado.


Agente Orquestrador Objetivo => Receber a solicitação pelo agendador, após a solicitação pegar no banco de dados para o agente que vai gerar a Receita, recebe o resultado  e o modo de preparo e encaminhar para o agente seguinte para gerar as imagens do modo de preparo.





Agente Gerador de HTML.  Objetivo => Receber do Oequestrador As imagens geradas, os Texto de Ingreditentes e o modo de preparo, recebendo isso, voce sera responsavel por gerar uma micro pagina com o modo de preparo em formato de iamgem em carrossel , e uma seçao com os ingredientes ordenados e e outra seção com o modo de preparo ordenado , e uma seção com a imagem do produto do cliente utilizado. Salvar em banco de dados o HTML.

Agente Gerador de Imagem do mode de preparo  Objetivo => Recebe do Orquestrador o modo de preparo as Imagens de referencias gerar um Passo a Passo do modo  de preparo utilizando, Imagens do produto e Identidade do cliente  e imagens dos ingredientes, o objetivo nao e so ter imagens repetidas e sim um passo a passo de cada etapa e a imagem executando aquele modo de preparo em Ordem.  RAG(Livros de receitas e modo de preparo, Achar algum Livro sobre Fotografia ? ) e Salvar no Banco de dados a referencia ou link da imagem


Nano Banana - Modelo Gerador de Imagem