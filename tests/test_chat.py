import pytest
from fastapi.testclient import TestClient

from app.main import app, get_llm_client, get_rate_limiter
from app.rate_limiter import RateLimiter
from tests.helpers import sid


class FakeLLMClient:
    def __init__(self):
        self.received_messages = None

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.received_messages = messages
        return "mocked reply"


@pytest.fixture
def fake_client():
    return FakeLLMClient()


@pytest.fixture
def client(fake_client):
    app.dependency_overrides[get_llm_client] = lambda: fake_client
    # Unrelated to rate limiting — isolate from the real global limiter so
    # this file's requests don't count against other test files' quota.
    app.dependency_overrides[get_rate_limiter] = lambda: RateLimiter(
        max_requests=1000, window_seconds=60
    )
    yield TestClient(app)
    app.dependency_overrides.pop(get_llm_client, None)
    app.dependency_overrides.pop(get_rate_limiter, None)


def test_chat_returns_model_reply(client):
    response = client.post(
        "/chat",
        json={"session_id": sid("test-chat-1"), "message": "What does your company do?"},
    )
    assert response.status_code == 200
    assert response.json() == {"reply": "mocked reply"}


def test_chat_sends_system_and_user_messages(client, fake_client):
    client.post("/chat", json={"session_id": sid("test-chat-2"), "message": "Hello"})
    roles = [m["role"] for m in fake_client.received_messages]
    assert roles == ["system", "user"]
    assert fake_client.received_messages[-1]["content"] == "Hello"


def test_chat_requires_message_field(client):
    response = client.post("/chat", json={"session_id": sid("test-chat-3")})
    assert response.status_code == 422


def test_chat_requires_session_id_field(client):
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 422


def test_chat_rejects_non_uuid_session_id(client):
    # Regression test: a short guessable session_id let one visitor hijack another's.
    response = client.post("/chat", json={"session_id": "1", "message": "Hello"})
    assert response.status_code == 422
