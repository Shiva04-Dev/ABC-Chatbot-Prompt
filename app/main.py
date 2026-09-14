from fastapi import Depends, FastAPI
from pydantic import BaseModel

from app.config import settings
from app.language import FALLBACK_NOTICE, resolve_language
from app.llm_client import AzureLLMClient, LLMClient
from app.prompts import build_system_prompt
from app.session_store import SessionStore, session_store

app = FastAPI(title="AfriBiz Connect Lite Assistant")

_llm_client = AzureLLMClient(settings)


def get_llm_client() -> LLMClient:
    return _llm_client


def get_session_store() -> SessionStore:
    return session_store


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    client: LLMClient = Depends(get_llm_client),
    sessions: SessionStore = Depends(get_session_store),
) -> ChatResponse:
    resolution = resolve_language(request.message, sessions.get_language(request.session_id))
    sessions.set_language(request.session_id, resolution.language)

    if resolution.used_fallback:
        # Don't guess-translate into an unsupported language (Section 6) —
        # reply directly, with no model call needed for this turn.
        return ChatResponse(reply=FALLBACK_NOTICE)

    messages = [
        {"role": "system", "content": build_system_prompt(resolution.language)},
        {"role": "user", "content": request.message},
    ]
    reply = client.complete(messages)
    return ChatResponse(reply=reply)
