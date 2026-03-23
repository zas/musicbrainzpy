"""MusicBrainzPy — Modern Python bindings for the MusicBrainz JSON API."""

from __future__ import annotations

from musicbrainzpy.annotation import annotation_to_markdown, annotation_to_text
from musicbrainzpy.auth import OAuthHandler, OAuthToken, build_authorization_url, generate_pkce
from musicbrainzpy.client import BrowseResult, MusicBrainzClient, SearchResult
from musicbrainzpy.enums import OAuthScope
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
    "OAuthHandler",
    "OAuthScope",
    "OAuthToken",
    "RateLimitedError",
    "SearchResult",
    "SyncMusicBrainzClient",
    "annotation_to_markdown",
    "annotation_to_text",
    "build_authorization_url",
    "generate_pkce",
]
