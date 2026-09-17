from types import SimpleNamespace

import pytest

from app.config import Settings
from app.llm_client import MAX_OUTPUT_TOKENS, RETRY_MAX_OUTPUT_TOKENS, AzureLLMClient


class FakeResponsesEndpoint:
    """Stands in for openai's `client.responses`, returning canned results
    in order so the retry-on-empty-output behaviour can be tested without
    hitting the real API."""

    def __init__(self, outputs: list[tuple[str, str]]):
        self._outputs = list(outputs)
        self.calls: list[dict] = []

    def create(self, model, input, max_output_tokens):
        self.calls.append(
            {"model": model, "input": input, "max_output_tokens": max_output_tokens}
        )
        output_text, status = self._outputs.pop(0)
        return SimpleNamespace(output_text=output_text, status=status)


def _client_with_fake_responses(outputs: list[tuple[str, str]]):
    client = AzureLLMClient(Settings())
    fake = FakeResponsesEndpoint(outputs)
    client._client = SimpleNamespace(responses=fake)
    return client, fake


def test_complete_returns_output_text_on_first_success():
    client, fake = _client_with_fake_responses([("Hello there", "completed")])

    result = client.complete([{"role": "user", "content": "hi"}])

    assert result == "Hello there"
    assert len(fake.calls) == 1
    assert fake.calls[0]["max_output_tokens"] == MAX_OUTPUT_TOKENS


def test_complete_retries_once_on_empty_output_and_returns_the_retry_result():
    # Reproduces what was observed live: GPT-5 mini's reasoning consumed the
    # whole first-attempt budget with nothing visible left over.
    client, fake = _client_with_fake_responses(
        [("", "incomplete"), ("Second try works", "completed")]
    )

    result = client.complete([{"role": "user", "content": "hi"}])

    assert result == "Second try works"
    assert len(fake.calls) == 2
    assert fake.calls[1]["max_output_tokens"] == RETRY_MAX_OUTPUT_TOKENS


def test_complete_raises_if_the_retry_is_also_empty():
    client, fake = _client_with_fake_responses(
        [("", "incomplete"), ("", "incomplete")]
    )

    with pytest.raises(RuntimeError, match="no output text"):
        client.complete([{"role": "user", "content": "hi"}])

    assert len(fake.calls) == 2
