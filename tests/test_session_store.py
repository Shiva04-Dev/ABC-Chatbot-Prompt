from app.session_store import MAX_HISTORY_MESSAGES, SessionStore


class FakeClock:
    """A controllable clock so TTL behaviour can be tested without sleeping."""

    def __init__(self, start: float = 0.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_get_history_empty_for_unknown_session():
    store = SessionStore()
    assert store.get_history("unknown") == []


def test_append_turn_stores_user_then_assistant():
    store = SessionStore()
    store.append_turn("s1", "hello", "hi there")
    assert store.get_history("s1") == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]


def test_get_history_returns_a_copy():
    store = SessionStore()
    store.append_turn("s1", "hello", "hi there")
    history = store.get_history("s1")
    history.append({"role": "user", "content": "injected"})
    assert store.get_history("s1") == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]


def test_history_caps_at_max_messages_keeping_most_recent():
    store = SessionStore()
    for i in range(10):
        store.append_turn("s1", f"question {i}", f"answer {i}")

    history = store.get_history("s1")
    assert len(history) == MAX_HISTORY_MESSAGES
    # Oldest exchanges dropped, most recent kept, order preserved.
    assert history[0] == {"role": "user", "content": "question 2"}
    assert history[-1] == {"role": "assistant", "content": "answer 9"}


def test_history_is_isolated_per_session():
    store = SessionStore()
    store.append_turn("a", "hello a", "hi a")
    store.append_turn("b", "hello b", "hi b")
    assert store.get_history("a") == [
        {"role": "user", "content": "hello a"},
        {"role": "assistant", "content": "hi a"},
    ]
    assert store.get_history("b") == [
        {"role": "user", "content": "hello b"},
        {"role": "assistant", "content": "hi b"},
    ]


def test_session_still_active_within_ttl():
    clock = FakeClock()
    store = SessionStore(ttl_seconds=1800, clock=clock)
    store.set_language("s1", "en")

    clock.advance(1799)

    assert store.get_language("s1") == "en"


def test_session_expires_after_ttl_of_inactivity():
    clock = FakeClock()
    store = SessionStore(ttl_seconds=1800, clock=clock)
    store.append_turn("s1", "hello", "hi there")
    store.set_language("s1", "en")

    clock.advance(1801)

    assert store.get_language("s1") is None
    assert store.get_history("s1") == []


def test_activity_resets_the_ttl_window():
    clock = FakeClock()
    store = SessionStore(ttl_seconds=1800, clock=clock)
    store.set_language("s1", "en")

    clock.advance(1700)
    store.append_turn("s1", "still here", "still here reply")  # resets the clock
    clock.advance(1700)

    # 1700s since the last activity, well under the 1800s TTL.
    assert store.get_language("s1") == "en"


def test_purge_expired_removes_only_stale_sessions():
    clock = FakeClock()
    store = SessionStore(ttl_seconds=1800, clock=clock)
    store.set_language("stale", "en")

    clock.advance(1000)
    store.set_language("fresh", "en")

    clock.advance(900)  # stale: 1900s idle; fresh: 900s idle

    removed = store.purge_expired()

    assert removed == 1
    assert store.get_language("stale") is None
    assert store.get_language("fresh") == "en"
