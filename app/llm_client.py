import logging
from typing import Protocol

from openai import BadRequestError, OpenAI

from app.config import Settings

logger = logging.getLogger(__name__)


class ContentFilteredError(Exception):
    """Raised when content safety blocks the request itself — a guardrail
    doing its job, not a service failure."""


# Safety-net cap, not the primary length control (that's app/prompts.py's
# Style instruction). The model spends part of this budget on internal
# reasoning before any visible text — 300 was too tight and came back
# empty; 500 usually works but isn't guaranteed, hence the retry below.
MAX_OUTPUT_TOKENS = 800

# Used for one automatic retry if the first attempt returns no visible text.
RETRY_MAX_OUTPUT_TOKENS = 1500


class LLMClient(Protocol):
    """Anything that can turn a list of chat messages into a reply string."""

    def complete(self, messages: list[dict[str, str]]) -> str: ...


class AzureLLMClient:
    """Thin wrapper around Azure's OpenAI-compatible v1 Responses API.

    Construction never touches the network, so it's safe with placeholder
    settings — the real call only happens in `complete`.
    """

    def __init__(self, settings: Settings):
        self._client = OpenAI(
            base_url=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
        )
        self._deployment = settings.azure_openai_deployment

    def _create(self, messages: list[dict[str, str]], max_output_tokens: int):
        try:
            return self._client.responses.create(
                model=self._deployment,
                input=messages,
                max_output_tokens=max_output_tokens,
            )
        except BadRequestError as exc:
            # code == "content_filter" means content safety blocked this,
            # not a service failure — let callers handle it distinctly.
            if getattr(exc, "code", None) == "content_filter":
                raise ContentFilteredError(str(exc)) from exc
            raise

    def complete(self, messages: list[dict[str, str]]) -> str:
        response = self._create(messages, MAX_OUTPUT_TOKENS)
        if response.output_text:
            return response.output_text

        # Reasoning consumed the whole budget with nothing visible left —
        # retry once with more headroom rather than return empty.
        logger.warning(
            "Empty output_text at max_output_tokens=%d (status=%r); retrying at %d",
            MAX_OUTPUT_TOKENS,
            response.status,
            RETRY_MAX_OUTPUT_TOKENS,
        )
        retry_response = self._create(messages, RETRY_MAX_OUTPUT_TOKENS)
        if retry_response.output_text:
            return retry_response.output_text

        logger.error(
            "Empty output_text again after retry at max_output_tokens=%d (status=%r)",
            RETRY_MAX_OUTPUT_TOKENS,
            retry_response.status,
        )
        raise RuntimeError(
            "Model returned no output text after a retry "
            f"(status={retry_response.status!r})"
        )
