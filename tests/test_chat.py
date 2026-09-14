import pytest
from fastapi.testclient import TestClient

from app.main import app, get_llm_client


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
    yield TestClient(app)
    app.dependency_overrides.pop(get_llm_client, None)


def test_chat_returns_model_reply(client):
    response = client.post(
        "/chat", json={"session_id": "test-chat-1", "message": "What does AfriBiz Connect do?"}
    )
    assert response.status_code == 200
    assert response.json() == {"reply": "mocked reply"}


def test_chat_sends_system_and_user_messages(client, fake_client):
    client.post("/chat", json={"session_id": "test-chat-2", "message": "Hello"})
    roles = [m["role"] for m in fake_client.received_messages]
    assert roles == ["system", "user"]
    assert fake_client.received_messages[-1]["content"] == "Hello"


def test_chat_requires_message_field(client):
    response = client.post("/chat", json={"session_id": "test-chat-3"})
    assert response.status_code == 422


def test_chat_requires_session_id_field(client):
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 422
