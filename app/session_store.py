import time
from typing import Callable

# 8 exchanges (1 user + 1 assistant message each) — see Section 8 of the project spec.
MAX_HISTORY_MESSAGES = 16

# A session with no activity for this long is treated as gone — one visit
# to the site is one session, and it isn't meant to be resumed later.
SESSION_TTL_SECONDS = 30 * 60


class SessionStore:
    """Per-session state, keyed by session_id.

    In-memory for now — and, given sessions are meant to live only as long
    as one site visit and never need to survive a restart, in-memory is the
    intended long-term design here, not just an MVP stopgap (Section 12.3
    resolved). Kept behind this interface so it can still be swapped later
    if that assumption ever changes (e.g. horizontal scaling).
    """

    def __init__(
        self,
        ttl_seconds: float = SESSION_TTL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._language_by_session: dict[str, str] = {}
        self._history_by_session: dict[str, list[dict[str, str]]] = {}
        self._last_active: dict[str, float] = {}

    def _is_expired(self, session_id: str, now: float) -> bool:
        last_active = self._last_active.get(session_id)
        return last_active is not None and (now - last_active) > self._ttl_seconds

    def _touch(self, session_id: str, now: float) -> None:
        self._last_active[session_id] = now

    def _forget(self, session_id: str) -> None:
        self._language_by_session.pop(session_id, None)
        self._history_by_session.pop(session_id, None)
        self._last_active.pop(session_id, None)

    def get_language(self, session_id: str) -> str | None:
        now = self._clock()
        if self._is_expired(session_id, now):
            self._forget(session_id)
            return None
        return self._language_by_session.get(session_id)

    def set_language(self, session_id: str, language: str) -> None:
        self._language_by_session[session_id] = language
        self._touch(session_id, self._clock())

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        now = self._clock()
        if self._is_expired(session_id, now):
            self._forget(session_id)
            return []
        return list(self._history_by_session.get(session_id, []))

    def append_turn(self, session_id: str, user_message: str, assistant_reply: str) -> None:
        history = self._history_by_session.setdefault(session_id, [])
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": assistant_reply})
        if len(history) > MAX_HISTORY_MESSAGES:
            del history[: len(history) - MAX_HISTORY_MESSAGES]
        self._touch(session_id, self._clock())

    def purge_expired(self) -> int:
        """Drop sessions idle past the TTL, reclaiming memory for visitors
        who never come back (a lazy check alone would leave them sitting in
        memory forever). Returns the number of sessions removed."""
        now = self._clock()
        expired = [
            session_id
            for session_id, last_active in self._last_active.items()
            if (now - last_active) > self._ttl_seconds
        ]
        for session_id in expired:
            self._forget(session_id)
        return len(expired)


session_store = SessionStore()
