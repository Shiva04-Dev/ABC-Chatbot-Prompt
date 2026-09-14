import pytest
from fastapi.testclient import TestClient

from app.main import app, get_llm_client
from tests.sample_scope_questions import IN_SCOPE_QUESTIONS, OUT_OF_SCOPE_QUESTIONS

ALL_SAMPLE_QUESTIONS = IN_SCOPE_QUESTIONS + OUT_OF_SCOPE_QUESTIONS


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
def client(recording_client):
    app.dependency_overrides[get_llm_client] = lambda: recording_client
    yield TestClient(app)
    app.dependency_overrides.pop(get_llm_client, None)


def test_every_sample_question_gets_the_scope_locked_prompt(client, recording_client):
    # Each question gets its own session — this test is about the scope-lock
    # prompt, not history accumulation (see test_chat_history.py for that).
    for index, question in enumerate(ALL_SAMPLE_QUESTIONS):
        response = client.post(
            "/chat",
            json={"session_id": f"test-chat-scope-session-{index}", "message": question},
        )
        assert response.status_code == 200

    for call, question in zip(recording_client.calls, ALL_SAMPLE_QUESTIONS):
        system_message, user_message = call
        assert system_message["role"] == "system"
        assert "only discuss AfriBiz Connect" in system_message["content"]
        assert user_message == {"role": "user", "content": question}
