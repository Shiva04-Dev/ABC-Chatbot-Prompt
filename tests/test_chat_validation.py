import pytest
from fastapi.testclient import TestClient

from app.main import app, get_llm_client, get_rate_limiter, get_session_store
from app.rate_limiter import RateLimiter
from app.session_store import SessionStore


class FakeLLMClient:
    def complete(self, messages: list[dict[str, str]]) -> str:
        return "mocked reply"


@pytest.fixture
def client():
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient()
    app.dependency_overrides[get_session_store] = lambda: SessionStore()
    app.dependency_overrides[get_rate_limiter] = lambda: RateLimiter(
        max_requests=1000, window_seconds=60
    )
    yield TestClient(app)
    app.dependency_overrides.pop(get_llm_client, None)
    app.dependency_overrides.pop(get_session_store, None)
    app.dependency_overrides.pop(get_rate_limiter, None)


def test_empty_message_is_rejected(client):
    response = client.post("/chat", json={"session_id": "s1", "message": ""})
    assert response.status_code == 422


def test_overlong_message_is_rejected(client):
    response = client.post("/chat", json={"session_id": "s1", "message": "a" * 2001})
    assert response.status_code == 422


def test_message_at_the_limit_is_accepted(client):
    response = client.post("/chat", json={"session_id": "s1", "message": "a" * 2000})
    assert response.status_code == 200


def test_empty_session_id_is_rejected(client):
    response = client.post("/chat", json={"session_id": "", "message": "Hello"})
    assert response.status_code == 422


def test_overlong_session_id_is_rejected(client):
    response = client.post("/chat", json={"session_id": "a" * 129, "message": "Hello"})
    assert response.status_code == 422
