from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"
    assert "db_url" in body
    assert "qdrant_host" in body
