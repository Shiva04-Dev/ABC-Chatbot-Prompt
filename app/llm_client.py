from typing import Protocol

from openai import OpenAI

from app.config import Settings

# Safety-net cap on reply length, not the primary length control (that's the
# "Style" instruction in app/prompts.py telling the model to be concise).
# GPT-5 mini is a reasoning model that spends part of this budget on internal
# reasoning tokens before any visible text — empirically, 300 wasn't enough
# and came back essentially empty; 500 completed reliably. Keeping real
# headroom above that measured threshold rather than trying to use this to
# tightly control length, since a too-low cap fails as a silent empty reply,
# not a graceful truncation.
MAX_OUTPUT_TOKENS = 800


class LLMClient(Protocol):
    """Anything that can turn a list of chat messages into a reply string."""

    def complete(self, messages: list[dict[str, str]]) -> str: ...


class AzureLLMClient:
    """Thin wrapper around Azure's OpenAI-compatible v1 Responses API call
    (see Section 5 of the project spec).

    Construction never touches the network, so this is safe to instantiate
    with placeholder settings — the real call only happens in `complete`.
    """

    def __init__(self, settings: Settings):
        self._client = OpenAI(
            base_url=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
        )
        self._deployment = settings.azure_openai_deployment

    def complete(self, messages: list[dict[str, str]]) -> str:
        response = self._client.responses.create(
            model=self._deployment,
            input=messages,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )
        return response.output_text
