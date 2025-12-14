import pytest
from datetime import datetime

from src.models.produtos import ProdutoClienteTable, ProdutoCreate, ProdutoOut
from src.models.ingredientes import IngredienteTable, IngredienteCreate, IngredienteOut
from src.models.receitas import ReceitaTable, ReceitaCreate, ReceitaOut, ImagemPasso
from src.models.imagens import ImagemTable, ImagemCreate, ImagemOut
from src.models.tasks import TaskTable, TaskCreate, TaskOut
from src.models.vectors import VectorTable, VectorCreate, VectorOut


class TestProdutoModels:
    def test_produto_table_creation(self, test_session):
        produto = ProdutoClienteTable(
            nome_produto="Leite Condensado",
            tipo_produto="Laticínio",
            descricao="Leite condensado tradicional",
        )
        test_session.add(produto)
        test_session.commit()
        test_session.refresh(produto)

        assert produto.id_produto is not None
        assert produto.nome_produto == "Leite Condensado"
        assert produto.tipo_produto == "Laticínio"

    def test_produto_create_schema(self):
        payload = ProdutoCreate(
            nome_produto="Creme de Leite",
            tipo_produto="Laticínio",
            descricao="Creme de leite fresco",
        )
        assert payload.nome_produto == "Creme de Leite"
        assert payload.tipo_produto == "Laticínio"

    def test_produto_out_schema(self):
        out = ProdutoOut(
            id=1,
            nome="Leite",
            tipo="Laticínio",
            descricao="Leite integral",
        )
        assert out.id == 1
        assert out.nome == "Leite"


class TestIngredienteModels:
    def test_ingrediente_table_creation(self, test_session):
        ingrediente = IngredienteTable(
            nome_singular="Ovo",
            nome_plural="Ovos",
            tipo_ingrediente="Proteína",
            descricao="Ovo de galinha",
        )
        test_session.add(ingrediente)
        test_session.commit()
        test_session.refresh(ingrediente)

        assert ingrediente.id_ingrediente is not None
        assert ingrediente.nome_singular == "Ovo"
        assert ingrediente.nome_plural == "Ovos"

    def test_ingrediente_create_schema(self):
        payload = IngredienteCreate(
            nome_singular="Açúcar",
            nome_plural="Açúcares",
            tipo_ingrediente="Doce",
        )
        assert payload.nome_singular == "Açúcar"

    def test_ingrediente_out_schema(self):
        out = IngredienteOut(
            id=1,
            nome_singular="Sal",
            nome_plural="Sais",
            tipo="Tempero",
        )
        assert out.id == 1
        assert out.nome_singular == "Sal"


class TestReceitaModels:
    def test_receita_table_creation(self, test_session):
        produto = ProdutoClienteTable(nome_produto="Teste")
        test_session.add(produto)
        test_session.commit()
        test_session.refresh(produto)

        receita = ReceitaTable(
            id_produto=produto.id_produto,
            status="pending",
        )
        test_session.add(receita)
        test_session.commit()
        test_session.refresh(receita)

        assert receita.id_receita is not None
        assert receita.status == "pending"
        assert receita.id_produto == produto.id_produto

    def test_receita_create_schema(self):
        payload = ReceitaCreate(
            id_produto=1,
            descricao_cliente="Receita para festa",
        )
        assert payload.id_produto == 1
        assert payload.descricao_cliente == "Receita para festa"

    def test_receita_out_schema(self):
        out = ReceitaOut(
            id=1,
            status="done",
            json_ingredientes=[{"nome": "Leite"}],
            json_modo_preparo=["Passo 1"],
            imagens=[],
        )
        assert out.id == 1
        assert out.status == "done"

    def test_imagem_passo_schema(self):
        img = ImagemPasso(
            step_index=0,
            url="http://example.com/img.png",
        )
        assert img.step_index == 0


class TestImagemModels:
    def test_imagem_table_creation(self, test_session):
        produto = ProdutoClienteTable(nome_produto="Teste")
        test_session.add(produto)
        test_session.commit()

        receita = ReceitaTable(id_produto=produto.id_produto, status="pending")
        test_session.add(receita)
        test_session.commit()
        test_session.refresh(receita)

        imagem = ImagemTable(
            id_receita=receita.id_receita,
            step_index=0,
            url="media/receitas/1/step_0.png",
            prompt_meta="Fotografia de alimento",
            seed="12345",
        )
        test_session.add(imagem)
        test_session.commit()
        test_session.refresh(imagem)

        assert imagem.id is not None
        assert imagem.step_index == 0
        assert imagem.url == "media/receitas/1/step_0.png"

    def test_imagem_create_schema(self):
        payload = ImagemCreate(
            id_receita=1,
            step_index=0,
            url="media/receitas/1/step_0.png",
        )
        assert payload.id_receita == 1
        assert payload.step_index == 0


class TestTaskModels:
    def test_task_table_creation(self, test_session):
        produto = ProdutoClienteTable(nome_produto="Teste")
        test_session.add(produto)
        test_session.commit()

        receita = ReceitaTable(id_produto=produto.id_produto, status="pending")
        test_session.add(receita)
        test_session.commit()
        test_session.refresh(receita)

        task = TaskTable(
            id_receita=receita.id_receita,
            type="recipe",
            status="running",
        )
        test_session.add(task)
        test_session.commit()
        test_session.refresh(task)

        assert task.id is not None
        assert task.type == "recipe"
        assert task.status == "running"

    def test_task_create_schema(self):
        payload = TaskCreate(
            id_receita=1,
            type="image",
            status="pending",
        )
        assert payload.type == "image"


class TestVectorModels:
    def test_vector_table_creation(self, test_session):
        produto = ProdutoClienteTable(nome_produto="Teste")
        test_session.add(produto)
        test_session.commit()

        receita = ReceitaTable(id_produto=produto.id_produto, status="pending")
        test_session.add(receita)
        test_session.commit()
        test_session.refresh(receita)

        vector = VectorTable(
            id_receita=receita.id_receita,
            kind="ingrediente",
            qdrant_id="abc-123",
            payload='{"text": "Leite condensado"}',
        )
        test_session.add(vector)
        test_session.commit()
        test_session.refresh(vector)

        assert vector.id is not None
        assert vector.kind == "ingrediente"
        assert vector.qdrant_id == "abc-123"

    def test_vector_create_schema(self):
        payload = VectorCreate(
            id_receita=1,
            kind="step",
            qdrant_id="xyz-789",
        )
        assert payload.kind == "step"
