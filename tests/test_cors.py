import pytest
from fastapi.testclient import TestClient

from app.main import app, get_llm_client, get_rate_limiter
from app.rate_limiter import RateLimiter


class FakeLLMClient:
    def complete(self, messages: list[dict[str, str]]) -> str:
        return "mocked reply"


@pytest.fixture
def client():
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient()
    app.dependency_overrides[get_rate_limiter] = lambda: RateLimiter(
        max_requests=1000, window_seconds=60
    )
    yield TestClient(app)
    app.dependency_overrides.pop(get_llm_client, None)
    app.dependency_overrides.pop(get_rate_limiter, None)


def test_vercel_production_origin_is_allowed(client):
    response = client.post(
        "/chat",
        json={"session_id": "cors-1", "message": "Hello"},
        headers={"Origin": "https://afribiz-test-ui.vercel.app"},
    )
    assert response.headers["access-control-allow-origin"] == "https://afribiz-test-ui.vercel.app"


def test_vercel_preview_deployment_origin_is_allowed(client):
    response = client.post(
        "/chat",
        json={"session_id": "cors-2", "message": "Hello"},
        headers={"Origin": "https://afribiz-test-ui-git-feature-shiv.vercel.app"},
    )
    assert (
        response.headers["access-control-allow-origin"]
        == "https://afribiz-test-ui-git-feature-shiv.vercel.app"
    )


def test_localhost_origin_is_allowed_for_testing_the_test_ui(client):
    response = client.post(
        "/chat",
        json={"session_id": "cors-4", "message": "Hello"},
        headers={"Origin": "http://localhost:5500"},
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5500"


def test_unrelated_origin_is_not_allowed(client):
    response = client.post(
        "/chat",
        json={"session_id": "cors-3", "message": "Hello"},
        headers={"Origin": "https://evil.example.com"},
    )
    assert "access-control-allow-origin" not in response.headers
