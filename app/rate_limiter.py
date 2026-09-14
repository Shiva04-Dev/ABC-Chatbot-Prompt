import time
from typing import Callable

# Fixed-window limiter: simple and O(1) per key, appropriate for "basic
# hardening" on a single-instance deployment (a sliding-window log would be
# more precise but isn't needed here).
DEFAULT_MAX_REQUESTS = 20
DEFAULT_WINDOW_SECONDS = 60.0


class RateLimiter:
    """Per-key fixed-window rate limiter, keyed by client IP in practice."""

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

    def is_allowed(self, key: str) -> bool:
        now = self._clock()
        window_start = self._window_start.get(key)

        if window_start is None or (now - window_start) >= self._window_seconds:
            self._window_start[key] = now
            self._request_count[key] = 1
            return True

        count = self._request_count.get(key, 0) + 1
        self._request_count[key] = count
        return count <= self._max_requests

    def purge_stale(self) -> int:
        """Drop windows that have already elapsed, so keys seen once
        (e.g. one-off visitor IPs) don't sit in memory forever."""
        now = self._clock()
        stale_keys = [
            key
            for key, window_start in self._window_start.items()
            if (now - window_start) >= self._window_seconds
        ]
        for key in stale_keys:
            self._window_start.pop(key, None)
            self._request_count.pop(key, None)
        return len(stale_keys)
