import pytest


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "db_url" in response.json()
    assert "qdrant_host" in response.json()
