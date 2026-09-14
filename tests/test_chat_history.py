import pytest
from fastapi.testclient import TestClient

from app.main import app, get_llm_client, get_rate_limiter, get_session_store
from app.rate_limiter import RateLimiter
from app.session_store import MAX_HISTORY_MESSAGES, SessionStore


class RecordingLLMClient:
    def __init__(self):
        self.calls: list[list[dict[str, str]]] = []
        self._reply_count = 0

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(messages)
        self._reply_count += 1
        return f"reply {self._reply_count}"


@pytest.fixture
def recording_client():
    return RecordingLLMClient()


@pytest.fixture
def sessions():
    return SessionStore()


@pytest.fixture
def client(recording_client, sessions):
    app.dependency_overrides[get_llm_client] = lambda: recording_client
    app.dependency_overrides[get_session_store] = lambda: sessions
    app.dependency_overrides[get_rate_limiter] = lambda: RateLimiter(
        max_requests=1000, window_seconds=60
    )
    yield TestClient(app)
    app.dependency_overrides.pop(get_llm_client, None)
    app.dependency_overrides.pop(get_session_store, None)
    app.dependency_overrides.pop(get_rate_limiter, None)


def test_first_turn_has_no_history(client, recording_client):
    client.post("/chat", json={"session_id": "s1", "message": "Hello"})
    messages = recording_client.calls[0]
    assert len(messages) == 2  # system + current user message only
    assert messages[-1] == {"role": "user", "content": "Hello"}


def test_second_turn_includes_prior_exchange_as_history(client, recording_client):
    client.post("/chat", json={"session_id": "s1", "message": "Hello"})
    client.post("/chat", json={"session_id": "s1", "message": "Tell me more"})

    second_call = recording_client.calls[1]
    assert second_call[0]["role"] == "system"
    assert second_call[1] == {"role": "user", "content": "Hello"}
    assert second_call[2] == {"role": "assistant", "content": "reply 1"}
    assert second_call[3] == {"role": "user", "content": "Tell me more"}


def test_history_persisted_in_session_store_after_reply(client, sessions):
    client.post("/chat", json={"session_id": "s1", "message": "Hello"})
    assert sessions.get_history("s1") == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "reply 1"},
    ]


def test_history_stays_capped_across_many_turns(client, sessions):
    for i in range(10):
        client.post("/chat", json={"session_id": "s1", "message": f"message {i}"})

    assert len(sessions.get_history("s1")) == MAX_HISTORY_MESSAGES


def test_history_is_not_shared_across_sessions(client, sessions):
    client.post("/chat", json={"session_id": "a", "message": "Hello from a"})
    client.post("/chat", json={"session_id": "b", "message": "Hello from b"})

    assert sessions.get_history("a") == [
        {"role": "user", "content": "Hello from a"},
        {"role": "assistant", "content": "reply 1"},
    ]
    assert sessions.get_history("b") == [
        {"role": "user", "content": "Hello from b"},
        {"role": "assistant", "content": "reply 2"},
    ]
