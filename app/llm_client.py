from typing import Protocol

from openai import AzureOpenAI

from app.config import Settings


class LLMClient(Protocol):
    """Anything that can turn a list of chat messages into a reply string."""

    def complete(self, messages: list[dict[str, str]]) -> str: ...


class AzureLLMClient:
    """Thin wrapper around the Azure OpenAI chat-completion call (CLAUDE.md Section 5).

    Construction never touches the network, so this is safe to instantiate
    with placeholder settings — the real call only happens in `complete`.
    """

    def __init__(self, settings: Settings):
        self._client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
        self._deployment = settings.azure_openai_deployment

    def complete(self, messages: list[dict[str, str]]) -> str:
        response = self._client.chat.completions.create(
            model=self._deployment,
            messages=messages,
        )
        return response.choices[0].message.content
