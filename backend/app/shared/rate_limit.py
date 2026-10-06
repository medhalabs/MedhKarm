"""A small sliding-window limiter for public endpoints (the waitlist, share views). In memory:
each API process counts for itself, which is enough to stop a script hammering one form."""

import time
from collections import defaultdict, deque
from collections.abc import Callable


class RateLimiter:
    def __init__(
        self, limit: int, seconds: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._limit = limit
        self._seconds = seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        """Counts one attempt for `key`; False when it has used up its attempts in the window."""
        now = self._clock()
        hits = self._hits[key]
        while hits and now - hits[0] >= self._seconds:
            hits.popleft()
        if len(hits) >= self._limit:
            return False
        hits.append(now)
        if not hits:  # pragma: no cover
            self._hits.pop(key, None)
        return True
