import pytest
from fastapi.testclient import TestClient

from app.main import app, get_llm_client, get_rate_limiter
from app.rate_limiter import RateLimiter


class FailingLLMClient:
    def complete(self, messages: list[dict[str, str]]) -> str:
        raise RuntimeError("simulated model failure")


@pytest.fixture
def client():
    app.dependency_overrides[get_llm_client] = lambda: FailingLLMClient()
    app.dependency_overrides[get_rate_limiter] = lambda: RateLimiter(
        max_requests=1000, window_seconds=60
    )
    yield TestClient(app)
    app.dependency_overrides.pop(get_llm_client, None)
    app.dependency_overrides.pop(get_rate_limiter, None)


def test_model_failure_returns_a_clean_502(client):
    response = client.post("/chat", json={"session_id": "err-1", "message": "Hello"})
    assert response.status_code == 502
    assert "unavailable" in response.json()["detail"]


def test_model_failure_response_still_carries_cors_header(client):
    # Regression test: an unhandled exception used to skip CORS entirely,
    # which browsers report as a misleading "blocked by CORS policy" error
    # instead of the real (502) failure — found via live testing the M7 UI.
    response = client.post(
        "/chat",
        json={"session_id": "err-2", "message": "Hello"},
        headers={"Origin": "http://localhost:5500"},
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5500"
