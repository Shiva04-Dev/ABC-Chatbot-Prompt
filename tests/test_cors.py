import pytest
from fastapi.testclient import TestClient

from app.main import app, get_llm_client


class FakeLLMClient:
    def complete(self, messages: list[dict[str, str]]) -> str:
        return "mocked reply"


@pytest.fixture
def client():
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient()
    yield TestClient(app)
    app.dependency_overrides.pop(get_llm_client, None)


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


def test_unrelated_origin_is_not_allowed(client):
    response = client.post(
        "/chat",
        json={"session_id": "cors-3", "message": "Hello"},
        headers={"Origin": "https://evil.example.com"},
    )
    assert "access-control-allow-origin" not in response.headers
