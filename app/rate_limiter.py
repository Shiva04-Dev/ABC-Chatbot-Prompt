import threading
import time
from typing import Callable

# Fixed-window limiter: simple and O(1) per key.
DEFAULT_MAX_REQUESTS = 20
DEFAULT_WINDOW_SECONDS = 60.0


class RateLimiter:
    """Per-key fixed-window rate limiter, keyed by client IP.

    Locked because FastAPI runs sync endpoints in a threadpool, so
    concurrent calls for the same key are possible (a pentest found this
    race let concurrent requests bypass the limit).
    """

    def __init__(
        self,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        window_seconds: float = DEFAULT_WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._clock = clock
        self._window_start: dict[str, float] = {}
        self._request_count: dict[str, int] = {}
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        now = self._clock()
        with self._lock:
            window_start = self._window_start.get(key)

            if window_start is None or (now - window_start) >= self._window_seconds:
                self._window_start[key] = now
                self._request_count[key] = 1
                return True

            count = self._request_count.get(key, 0) + 1
            self._request_count[key] = count
            return count <= self._max_requests

    def purge_stale(self) -> int:
        """Drop elapsed windows so one-off keys don't sit in memory forever."""
        now = self._clock()
        with self._lock:
            stale_keys = [
                key
                for key, window_start in self._window_start.items()
                if (now - window_start) >= self._window_seconds
            ]
            for key in stale_keys:
                self._window_start.pop(key, None)
                self._request_count.pop(key, None)
            return len(stale_keys)
