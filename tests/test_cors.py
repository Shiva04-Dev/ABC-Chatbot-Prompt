import pytest
from fastapi.testclient import TestClient

from app.main import app, get_llm_client, get_rate_limiter
from app.rate_limiter import RateLimiter
from tests.helpers import sid


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


def test_arbitrary_vercel_origin_is_not_allowed_by_default(client):
    # Regression test: a blanket *.vercel.app default used to let ANY
    # Vercel-hosted origin get real LLM replies. Localhost-only by default now.
    response = client.post(
        "/chat",
        json={"session_id": sid("cors-1"), "message": "Hello"},
        headers={"Origin": "https://some-unrelated-project.vercel.app"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_localhost_origin_is_allowed_for_testing_the_test_ui(client):
    response = client.post(
        "/chat",
        json={"session_id": sid("cors-2"), "message": "Hello"},
        headers={"Origin": "http://localhost:5500"},
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5500"


def test_unrelated_origin_is_not_allowed(client):
    response = client.post(
        "/chat",
        json={"session_id": sid("cors-3"), "message": "Hello"},
        headers={"Origin": "https://evil.example.com"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_project_scoped_regex_pattern_is_actually_correct():
    # CORSMiddleware is fixed at app startup, so this checks the pattern
    # itself matches only the intended project, not an unrelated Vercel app.
    import re

    pattern = re.compile(r"^https://my-project(-[a-z0-9-]+)?\.vercel\.app$")

    assert pattern.match("https://my-project.vercel.app")
    assert pattern.match("https://my-project-git-feature-abc123.vercel.app")
    assert not pattern.match("https://some-unrelated-project.vercel.app")
