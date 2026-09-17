from types import SimpleNamespace

import httpx2
import pytest
from openai import BadRequestError

from app.config import Settings
from app.llm_client import (
    MAX_OUTPUT_TOKENS,
    RETRY_MAX_OUTPUT_TOKENS,
    AzureLLMClient,
    ContentFilteredError,
)


def _content_filter_error() -> BadRequestError:
    response = httpx2.Response(400, request=httpx2.Request("POST", "https://example.com"))
    body = {"message": "The response was filtered", "code": "content_filter"}
    return BadRequestError("The response was filtered", response=response, body=body)


class RaisingResponsesEndpoint:
    def __init__(self, exc: Exception):
        self._exc = exc

    def create(self, model, input, max_output_tokens):
        raise self._exc


class FakeResponsesEndpoint:
    """Stands in for openai's `client.responses` to test retry-on-empty
    behaviour without hitting the real API."""

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


def test_content_filter_block_raises_content_filtered_error():
    # Confirmed live: content safety blocks with a 400 BadRequestError
    # (code "content_filter") — distinguishable from a genuine outage.
    client = AzureLLMClient(Settings())
    client._client = SimpleNamespace(responses=RaisingResponsesEndpoint(_content_filter_error()))

    with pytest.raises(ContentFilteredError):
        client.complete([{"role": "user", "content": "jailbreak attempt"}])


def test_other_bad_request_errors_are_not_swallowed_as_content_filtered():
    response = httpx2.Response(400, request=httpx2.Request("POST", "https://example.com"))
    other_error = BadRequestError(
        "Something else was wrong", response=response, body={"code": "invalid_request"}
    )
    client = AzureLLMClient(Settings())
    client._client = SimpleNamespace(responses=RaisingResponsesEndpoint(other_error))

    with pytest.raises(BadRequestError):
        client.complete([{"role": "user", "content": "hi"}])
