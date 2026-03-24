"""MusicBrainzPy — Modern Python bindings for the MusicBrainz JSON API."""

from __future__ import annotations

import logging
import os

from musicbrainzpy.annotation import annotation_to_markdown, annotation_to_text
from musicbrainzpy.auth import OAuthHandler, OAuthToken, build_authorization_url, generate_pkce
from musicbrainzpy.client import BrowseResult, MusicBrainzClient, SearchResult
from musicbrainzpy.coverart import CoverArtClient, SyncCoverArtClient
from musicbrainzpy.enums import OAuthScope
from musicbrainzpy.exceptions import (
    AuthenticationError,
    InvalidRequestError,
    MusicBrainzError,
    NotFoundError,
    RateLimitedError,
)
from musicbrainzpy.sync_client import SyncMusicBrainzClient

if os.environ.get("MUSICBRAINZPY_DEBUG"):
    _mblogger = logging.getLogger("musicbrainzpy")
    _mblogger.setLevel(logging.DEBUG)
    if not _mblogger.handlers:
        _handler = logging.StreamHandler()
        _handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
        _mblogger.addHandler(_handler)

__all__ = [
    "AuthenticationError",
    "BrowseResult",
    "CoverArtClient",
    "InvalidRequestError",
    "MusicBrainzClient",
    "MusicBrainzError",
    "NotFoundError",
    "OAuthHandler",
    "OAuthScope",
    "OAuthToken",
    "RateLimitedError",
    "SearchResult",
    "SyncCoverArtClient",
    "SyncMusicBrainzClient",
    "annotation_to_markdown",
    "annotation_to_text",
    "build_authorization_url",
    "generate_pkce",
]
