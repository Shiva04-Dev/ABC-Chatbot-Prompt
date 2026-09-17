import pytest
from fastapi.testclient import TestClient

from app.main import app, get_llm_client, get_rate_limiter, get_session_store
from app.rate_limiter import RateLimiter
from app.session_store import SessionStore
from tests.helpers import sid


class FakeLLMClient:
    def complete(self, messages: list[dict[str, str]]) -> str:
        return "mocked reply"


@pytest.fixture
def limiter():
    return RateLimiter(max_requests=2, window_seconds=60)


@pytest.fixture
def client(limiter):
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient()
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    app.dependency_overrides[get_session_store] = lambda: SessionStore()
    yield TestClient(app)
    app.dependency_overrides.pop(get_llm_client, None)
    app.dependency_overrides.pop(get_rate_limiter, None)
    app.dependency_overrides.pop(get_session_store, None)


def test_requests_within_the_limit_succeed(client):
    for _ in range(2):
        response = client.post("/chat", json={"session_id": sid("s1"), "message": "Hello"})
        assert response.status_code == 200


def test_requests_beyond_the_limit_are_rejected(client):
    for _ in range(2):
        client.post("/chat", json={"session_id": sid("s1"), "message": "Hello"})

    response = client.post("/chat", json={"session_id": sid("s1"), "message": "Hello"})
    assert response.status_code == 429


def test_limit_is_per_client_not_per_session(client):
    for _ in range(2):
        client.post("/chat", json={"session_id": sid("s1"), "message": "Hello"})

    # Same client IP, different session — still the same rate-limit key.
    response = client.post("/chat", json={"session_id": sid("s2"), "message": "Hello"})
    assert response.status_code == 429


def test_different_clients_are_limited_independently(client):
    for _ in range(2):
        client.post(
            "/chat",
            json={"session_id": sid("s1"), "message": "Hello"},
            headers={"X-Forwarded-For": "1.1.1.1"},
        )

    response = client.post(
        "/chat",
        json={"session_id": sid("s1"), "message": "Hello"},
        headers={"X-Forwarded-For": "2.2.2.2"},
    )
    assert response.status_code == 200


def test_spoofed_first_hop_does_not_bypass_rate_limit(client):
    # Regression test: varying the spoofable first X-Forwarded-For hop must
    # not bypass the limit — only the trusted last hop should matter.
    for fake_client_ip in ["9.9.9.9", "8.8.8.8"]:
        response = client.post(
            "/chat",
            json={"session_id": sid("s1"), "message": "Hello"},
            headers={"X-Forwarded-For": f"{fake_client_ip}, 10.0.0.1"},
        )
        assert response.status_code == 200

    response = client.post(
        "/chat",
        json={"session_id": sid("s1"), "message": "Hello"},
        headers={"X-Forwarded-For": "7.7.7.7, 10.0.0.1"},
    )
    assert response.status_code == 429


def test_health_endpoint_is_not_rate_limited(client):
    for _ in range(10):
        response = client.get("/health")
        assert response.status_code == 200
