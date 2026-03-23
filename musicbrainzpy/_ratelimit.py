"""Async rate limiter enforcing 1 request per second."""

from __future__ import annotations

import asyncio
import time


class RateLimiter:
    """Simple rate limiter: ensures at least `interval` seconds between requests."""

    def __init__(self, interval: float = 1.0) -> None:
        self._interval = interval
        self._last_request: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self._interval:
                await asyncio.sleep(self._interval - elapsed)
            self._last_request = time.monotonic()


class SyncRateLimiter:
    """Synchronous rate limiter for the sync client wrapper."""

    def __init__(self, interval: float = 1.0) -> None:
        self._interval = interval
        self._last_request: float = 0.0

    def acquire(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request
        if elapsed < self._interval:
            time.sleep(self._interval - elapsed)
        self._last_request = time.monotonic()
