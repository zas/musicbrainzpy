"""Exceptions for MusicBrainzPy."""

from __future__ import annotations


class MusicBrainzError(Exception):
    """Base exception for all MusicBrainz API errors."""


class NotFoundError(MusicBrainzError):
    """Entity not found (HTTP 404)."""


class RateLimitedError(MusicBrainzError):
    """Rate limit exceeded (HTTP 503)."""


class AuthenticationError(MusicBrainzError):
    """Authentication required or failed (HTTP 401)."""


class InvalidRequestError(MusicBrainzError):
    """Bad request (HTTP 400)."""
