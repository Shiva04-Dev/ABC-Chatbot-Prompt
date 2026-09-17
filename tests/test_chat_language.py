import pytest
from fastapi.testclient import TestClient

from app.language import FALLBACK_NOTICE
from app.main import app, get_llm_client, get_rate_limiter, get_session_store
from app.rate_limiter import RateLimiter
from app.session_store import SessionStore
from tests.helpers import sid


class RecordingLLMClient:
    def __init__(self):
        self.calls: list[list[dict[str, str]]] = []

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(messages)
        return "mocked reply"


@pytest.fixture
def recording_client():
    return RecordingLLMClient()


@pytest.fixture
def sessions():
    # Fresh, isolated store per test — the app's real session_store is a
    # process-wide singleton and must not leak state between tests.
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


def test_english_message_gets_english_directive(client, recording_client):
    client.post("/chat", json={"session_id": sid("s1"), "message": "Hello, can you help me?"})
    system_content = recording_client.calls[0][0]["content"]
    assert "Reply only in English." in system_content


def test_explicit_switch_then_session_persists_zulu(client, recording_client, sessions):
    client.post("/chat", json={"session_id": sid("s2"), "message": "khuluma isizulu"})
    # Second turn has no isiZulu markers at all — session must keep it isiZulu.
    client.post("/chat", json={"session_id": sid("s2"), "message": "ok thanks"})

    assert len(recording_client.calls) == 2
    for call in recording_client.calls:
        assert "Reply only in isiZulu." in call[0]["content"]
    assert sessions.get_language(sid("s2")) == "zu"


def test_third_language_gets_fallback_notice_without_calling_model(client, recording_client):
    response = client.post(
        "/chat", json={"session_id": sid("s3"), "message": "Bonjour, comment allez-vous?"}
    )
    assert response.status_code == 200
    assert response.json() == {"reply": FALLBACK_NOTICE}
    assert recording_client.calls == []


def test_sessions_are_independent(client, recording_client, sessions):
    client.post("/chat", json={"session_id": sid("en-session"), "message": "Hello there"})
    client.post("/chat", json={"session_id": sid("zu-session"), "message": "Sawubona, ngicela usizo"})

    assert sessions.get_language(sid("en-session")) == "en"
    assert sessions.get_language(sid("zu-session")) == "zu"
