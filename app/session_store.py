class SessionStore:
    """Per-session state, keyed by session_id.

    In-memory for now (Section 8's persistence backend is an open decision —
    Section 12.3). Holds only the resolved language for M4; M5 extends this
    same store with capped conversation history behind the same interface.
    """

    def __init__(self) -> None:
        self._language_by_session: dict[str, str] = {}

    def get_language(self, session_id: str) -> str | None:
        return self._language_by_session.get(session_id)

    def set_language(self, session_id: str, language: str) -> None:
        self._language_by_session[session_id] = language


session_store = SessionStore()
