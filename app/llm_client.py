import logging
from typing import Protocol

from openai import OpenAI

from app.config import Settings

logger = logging.getLogger(__name__)

# Safety-net cap on reply length, not the primary length control (that's the
# "Style" instruction in app/prompts.py telling the model to be concise).
# GPT-5 mini is a reasoning model that spends part of this budget on internal
# reasoning tokens before any visible text — empirically, 300 wasn't enough
# and came back essentially empty; 500 completed reliably most of the time.
# But this isn't fully deterministic: on a harder/more ambiguous input, an
# 800-token budget was once still entirely consumed by reasoning with no
# visible output — an identical retry then succeeded normally. So no fixed
# cap is guaranteed safe; see RETRY_MAX_OUTPUT_TOKENS below for how that's
# actually handled.
MAX_OUTPUT_TOKENS = 800

# Used for a single automatic retry if the first attempt comes back with no
# visible text (see complete() below) — more headroom than the first try,
# on the theory that a bit more room reduces the odds of hitting this twice.
RETRY_MAX_OUTPUT_TOKENS = 1500


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
        if response.output_text:
            return response.output_text

        # Reasoning consumed the whole budget with nothing visible left over
        # (real, observed behaviour — not hypothetical). One retry with more
        # headroom before giving up; never silently return an empty reply.
        logger.warning(
            "Empty output_text at max_output_tokens=%d (status=%r); retrying at %d",
            MAX_OUTPUT_TOKENS,
            response.status,
            RETRY_MAX_OUTPUT_TOKENS,
        )
        retry_response = self._client.responses.create(
            model=self._deployment,
            input=messages,
            max_output_tokens=RETRY_MAX_OUTPUT_TOKENS,
        )
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
