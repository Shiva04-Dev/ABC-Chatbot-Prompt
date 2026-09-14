import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.language import FALLBACK_NOTICE, resolve_language
from app.llm_client import AzureLLMClient, LLMClient
from app.prompts import build_system_prompt
from app.session_store import SessionStore, session_store

# How often the background sweep checks for idle sessions to drop. Well
# under the 30-minute TTL so expired sessions don't linger long in memory.
SESSION_SWEEP_INTERVAL_SECONDS = 5 * 60


async def _sweep_expired_sessions_periodically() -> None:
    while True:
        await asyncio.sleep(SESSION_SWEEP_INTERVAL_SECONDS)
        session_store.purge_expired()


@asynccontextmanager
async def lifespan(app: FastAPI):
    sweep_task = asyncio.create_task(_sweep_expired_sessions_periodically())
    try:
        yield
    finally:
        sweep_task.cancel()


app = FastAPI(title="AfriBiz Connect Lite Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()],
    allow_origin_regex=settings.cors_allowed_origin_regex or None,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

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
        sessions.append_turn(request.session_id, request.message, FALLBACK_NOTICE)
        return ChatResponse(reply=FALLBACK_NOTICE)

    history = sessions.get_history(request.session_id)
    messages = [
        {"role": "system", "content": build_system_prompt(resolution.language)},
        *history,
        {"role": "user", "content": request.message},
    ]
    reply = client.complete(messages)
    sessions.append_turn(request.session_id, request.message, reply)
    return ChatResponse(reply=reply)
