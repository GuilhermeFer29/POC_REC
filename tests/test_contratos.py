from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_get_produtos():
    resp = client.get("/produtos")
    assert resp.status_code == 200


def test_get_produto_by_id_200():
    resp = client.get("/produtos/1")
    assert resp.status_code == 404


def test_get_produto_by_id_404():
    resp = client.get("/produtos/9999")
    assert resp.status_code == 404


def test_get_ingredientes():
    resp = client.get("/ingredientes")
    assert resp.status_code == 200


def test_post_receitas_201():
    payload = {"id_produto": 1}
    resp = client.post("/receitas", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending"


def test_get_receita_404():
    resp = client.get("/receitas/9999")
    assert resp.status_code == 404
