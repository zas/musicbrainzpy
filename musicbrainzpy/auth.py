"""Authentication helpers for the MusicBrainz API.

Supports HTTP Digest authentication (current) and OAuth2 (recommended for new apps).
"""

from __future__ import annotations

import httpx


def make_digest_auth(username: str, password: str) -> httpx.DigestAuth:
    """Create an httpx DigestAuth instance for MusicBrainz API authentication.

    Args:
        username: MusicBrainz username.
        password: MusicBrainz password.
    """
    return httpx.DigestAuth(username, password)
