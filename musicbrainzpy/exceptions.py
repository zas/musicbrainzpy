"""Exceptions for MusicBrainzPy."""

from __future__ import annotations


class MusicBrainzError(Exception):
    """Base exception for all MusicBrainz API errors."""


class NotFoundError(MusicBrainzError):
    """Entity not found (HTTP 404)."""


class RateLimitedError(MusicBrainzError):
    """Rate limit exceeded (HTTP 429 or 503)."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class AuthenticationError(MusicBrainzError):
    """Authentication required or failed (HTTP 401)."""


class InvalidRequestError(MusicBrainzError):
    """Bad request (HTTP 400)."""
