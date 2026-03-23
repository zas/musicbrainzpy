"""MusicBrainzPy — Modern Python bindings for the MusicBrainz JSON API."""

from __future__ import annotations

from musicbrainzpy.client import BrowseResult, MusicBrainzClient, SearchResult
from musicbrainzpy.exceptions import (
    AuthenticationError,
    InvalidRequestError,
    MusicBrainzError,
    NotFoundError,
    RateLimitedError,
)
from musicbrainzpy.sync_client import SyncMusicBrainzClient

__all__ = [
    "AuthenticationError",
    "BrowseResult",
    "InvalidRequestError",
    "MusicBrainzClient",
    "MusicBrainzError",
    "NotFoundError",
    "RateLimitedError",
    "SearchResult",
    "SyncMusicBrainzClient",
]
