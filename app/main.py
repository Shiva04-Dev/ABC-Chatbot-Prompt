import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.language import FALLBACK_NOTICE, resolve_language
from app.llm_client import AzureLLMClient, ContentFilteredError, LLMClient
from app.prompts import build_system_prompt
from app.rate_limiter import RateLimiter
from app.session_store import SessionStore, session_store
from content.company import COMPANY_NAME

# How often the background sweep clears idle sessions / stale rate-limit windows.
SESSION_SWEEP_INTERVAL_SECONDS = 5 * 60

rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_max_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


async def _sweep_stale_state_periodically() -> None:
    while True:
        await asyncio.sleep(SESSION_SWEEP_INTERVAL_SECONDS)
        session_store.purge_expired()
        rate_limiter.purge_stale()


@asynccontextmanager
async def lifespan(app: FastAPI):
    sweep_task = asyncio.create_task(_sweep_stale_state_periodically())
    try:
        yield
    finally:
        sweep_task.cancel()


app = FastAPI(title=f"{COMPANY_NAME} Lite Assistant", lifespan=lifespan)

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


def get_rate_limiter() -> RateLimiter:
    return rate_limiter


def _client_key(request: Request) -> str:
    # Trust the LAST X-Forwarded-For hop (our proxy's), not the first
    # (client-controlled and spoofable — confirmed by a pentest).
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(
    request: Request, limiter: RateLimiter = Depends(get_rate_limiter)
) -> None:
    if not limiter.is_allowed(_client_key(request)):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please slow down and try again shortly.",
        )


SESSION_ID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


class ChatRequest(BaseModel):
    # Must be UUID-shaped — a guessable session_id let one visitor hijack
    # another's session (confirmed by a pentest).
    session_id: str = Field(pattern=SESSION_ID_PATTERN)
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str


# Shown when content safety blocks a message outright — a normal in-scope
# refusal, not an error.
CONTENT_FILTERED_REPLY = (
    "I'm not able to help with that. Let me know if you have any questions "
    f"about {COMPANY_NAME} and its services!"
)


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # A registered handler keeps CORS headers on error responses too.
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again shortly."},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    client: LLMClient = Depends(get_llm_client),
    sessions: SessionStore = Depends(get_session_store),
    _rate_limit_check: None = Depends(enforce_rate_limit),
) -> ChatResponse:
    resolution = resolve_language(request.message, sessions.get_language(request.session_id))
    sessions.set_language(request.session_id, resolution.language)

    if resolution.used_fallback:
        # Don't guess-translate into an unsupported language — reply directly.
        sessions.append_turn(request.session_id, request.message, FALLBACK_NOTICE)
        return ChatResponse(reply=FALLBACK_NOTICE)

    history = sessions.get_history(request.session_id)
    messages = [
        {"role": "system", "content": build_system_prompt(resolution.language)},
        *history,
        {"role": "user", "content": request.message},
    ]
    try:
        reply = client.complete(messages)
    except ContentFilteredError:
        # The platform correctly blocked this — not a failure.
        reply = CONTENT_FILTERED_REPLY
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="The AI service is currently unavailable. Please try again shortly.",
        ) from exc
    sessions.append_turn(request.session_id, request.message, reply)
    return ChatResponse(reply=reply)
