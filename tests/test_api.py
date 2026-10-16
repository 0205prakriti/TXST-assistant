from fastapi.testclient import TestClient
import memory.memory as memory
from api import app
import httpx
from groq import RateLimitError

client = TestClient(app)


def test_rate_limit_returns_actionable_error(monkeypatch):
    def limited(*args):
        raise RateLimitError("Rate limit", response=httpx.Response(429, request=httpx.Request("POST", "https://api.groq.com")), body=None)
    monkeypatch.setattr("api.answer", limited)
    response = client.post("/chat", json={"message": "How do I apply for aid?"})
    assert response.status_code == 429
    assert "try again" in response.json()["detail"]

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_chat_returns_valid_response(monkeypatch, tmp_path):
    monkeypatch.setattr(memory, "MEMORY_FILE", tmp_path / "sessions.json")
    monkeypatch.setattr("chat_service.route", lambda _: {"agent": "CAMPUS", "confidence": 0.9})
    monkeypatch.setattr("chat_service.campus.run", lambda message, history: "Library answer")
    response = client.post("/chat", json={"message": "Where is the library?"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "agent" in data
    assert "confidence" in data
    assert data["session_id"]
    assert client.get("/history", params={"session_id": data["session_id"]}).json()["history"][-1]["content"] == "Library answer"
    second = client.post("/chat", json={"message": "And its hours?", "session_id": data["session_id"]})
    assert second.json()["session_id"] == data["session_id"]
    assert len(client.get("/history", params={"session_id": data["session_id"]}).json()["history"]) == 4
    assert client.get("/history", params={"session_id": "another-session"}).json()["history"] == []

def test_get_history(monkeypatch, tmp_path):
    monkeypatch.setattr(memory, "MEMORY_FILE", tmp_path / "sessions.json")
    response = client.get("/history", params={"session_id": "one"})
    assert response.status_code == 200
    assert "history" in response.json()

def test_delete_history(monkeypatch, tmp_path):
    monkeypatch.setattr(memory, "MEMORY_FILE", tmp_path / "sessions.json")
    memory.save_history([{"role": "user", "content": "hello"}], "one")
    memory.save_history([{"role": "user", "content": "private"}], "two")
    response = client.delete("/history", params={"session_id": "one"})
    assert response.status_code == 200
    assert response.json()["status"] == "cleared"
    assert memory.load_history("one") == []
    assert len(memory.load_history("two")) == 1

def test_chat_stream_emits_sse_events(monkeypatch):
    def fake_stream(message, session_id=None):
        def gen():
            yield "Hello"
            yield " world"
        return {"agent": "CAMPUS", "confidence": 0.9, "session_id": "s1"}, gen()
    monkeypatch.setattr("api.answer_stream", fake_stream)
    response = client.get("/chat/stream", params={"message": "hi"})
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    assert '"type": "meta"' in body
    assert '"type": "token"' in body
    assert '"type": "done"' in body
    assert "Hello" in body
