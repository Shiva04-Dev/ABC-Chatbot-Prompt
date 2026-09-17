import threading

from app.rate_limiter import RateLimiter


class FakeClock:
    def __init__(self, start: float = 0.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_allows_requests_up_to_the_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    assert limiter.is_allowed("ip-1") is True
    assert limiter.is_allowed("ip-1") is True
    assert limiter.is_allowed("ip-1") is True


def test_blocks_requests_beyond_the_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        limiter.is_allowed("ip-1")
    assert limiter.is_allowed("ip-1") is False


def test_resets_after_the_window_elapses():
    clock = FakeClock()
    limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    limiter.is_allowed("ip-1")
    limiter.is_allowed("ip-1")
    assert limiter.is_allowed("ip-1") is False

    clock.advance(61)

    assert limiter.is_allowed("ip-1") is True


def test_keys_are_tracked_independently():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.is_allowed("ip-1") is True
    assert limiter.is_allowed("ip-2") is True
    assert limiter.is_allowed("ip-1") is False
    assert limiter.is_allowed("ip-2") is False


def test_is_allowed_is_thread_safe_under_concurrent_requests():
    # Concurrent calls for the same key are possible under FastAPI's
    # threadpool; without the lock this race lets requests bypass the limit.
    limiter = RateLimiter(max_requests=20, window_seconds=60)
    results: list[bool] = []
    results_lock = threading.Lock()

    def hit() -> None:
        allowed = limiter.is_allowed("same-key")
        with results_lock:
            results.append(allowed)

    threads = [threading.Thread(target=hit) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sum(results) == 20


def test_purge_stale_drops_elapsed_windows_only():
    clock = FakeClock()
    limiter = RateLimiter(max_requests=5, window_seconds=60, clock=clock)
    limiter.is_allowed("stale")

    clock.advance(30)
    limiter.is_allowed("fresh")

    clock.advance(31)  # stale: 61s old; fresh: 31s old

    removed = limiter.purge_stale()

    assert removed == 1
    # Confirm the fresh key's in-window count survived the purge.
    assert limiter.is_allowed("fresh") is True
