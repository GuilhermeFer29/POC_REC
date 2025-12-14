import pytest


def test_listar_produtos(client):
    response = client.get("/produtos")
    assert response.status_code == 200
    assert response.json() == []


def test_obter_produto_inexistente(client):
    response = client.get("/produtos/99999")
    assert response.status_code == 404


def test_listar_ingredientes(client):
    response = client.get("/ingredientes")
    assert response.status_code == 200
    assert response.json() == []


def test_obter_receita_inexistente(client):
    response = client.get("/receitas/99999")
    assert response.status_code == 404
