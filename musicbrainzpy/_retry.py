"""Retry helpers for transient HTTP failures."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

import httpx

from musicbrainzpy.exceptions import RateLimitedError

logger = logging.getLogger("musicbrainzpy")

#: Defaults
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0


def _retry_delay(exc: Exception, attempt: int, base_delay: float) -> float:
    """Compute delay: use Retry-After if available, otherwise exponential backoff."""
    if isinstance(exc, RateLimitedError) and exc.retry_after is not None:
        return exc.retry_after
    return base_delay * (2**attempt)


def _is_retryable(exc: Exception) -> bool:
    """Return True for transient errors worth retrying."""
    return isinstance(exc, (httpx.TransportError, RateLimitedError))


async def async_retry[T](
    func: Callable[[], Awaitable[T]],
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
) -> T:
    """Call *func* with retries on transient failures."""
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as exc:
            if not _is_retryable(exc) or attempt == max_retries:
                raise
            delay = _retry_delay(exc, attempt, base_delay)
            logger.debug("Retry %d/%d after %.1fs: %s", attempt + 1, max_retries, delay, exc)
            await asyncio.sleep(delay)
    raise AssertionError("unreachable")  # pragma: no cover


def sync_retry[T](
    func: Callable[[], T],
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
) -> T:
    """Call *func* with retries on transient failures (sync version)."""
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as exc:
            if not _is_retryable(exc) or attempt == max_retries:
                raise
            delay = _retry_delay(exc, attempt, base_delay)
            logger.debug("Retry %d/%d after %.1fs: %s", attempt + 1, max_retries, delay, exc)
            time.sleep(delay)
    raise AssertionError("unreachable")  # pragma: no cover
