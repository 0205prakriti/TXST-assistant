from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_chat_returns_valid_response():
    response = client.post("/chat", json={"message": "Where is the library?"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "agent" in data
    assert "confidence" in data

def test_get_history():
    response = client.get("/history")
    assert response.status_code == 200
    assert "history" in response.json()

def test_delete_history():
    response = client.delete("/history")
    assert response.status_code == 200
    assert response.json()["status"] == "cleared"