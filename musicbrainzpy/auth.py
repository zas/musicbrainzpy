"""Authentication helpers for the MusicBrainz API.

Supports HTTP Digest authentication and OAuth2 (recommended for new apps).
See https://musicbrainz.org/doc/Development/OAuth2 for the full spec.
"""

from __future__ import annotations

import hashlib
import secrets
import time
from base64 import urlsafe_b64encode
from dataclasses import dataclass, field

import httpx

DEFAULT_SERVER = "https://musicbrainz.org"

AUTHORIZE_URL = f"{DEFAULT_SERVER}/oauth2/authorize"
TOKEN_URL = f"{DEFAULT_SERVER}/oauth2/token"
REVOKE_URL = f"{DEFAULT_SERVER}/oauth2/revoke"
USERINFO_URL = f"{DEFAULT_SERVER}/oauth2/userinfo"


def _oauth_urls(server: str) -> tuple[str, str, str, str]:
    """Derive OAuth2 endpoint URLs from a server base URL.

    Args:
        server: Server base URL (e.g. ``"https://test.musicbrainz.org"``).

    Returns:
        Tuple of ``(authorize_url, token_url, revoke_url, userinfo_url)``.
    """
    s = server.rstrip("/")
    return (
        f"{s}/oauth2/authorize",
        f"{s}/oauth2/token",
        f"{s}/oauth2/revoke",
        f"{s}/oauth2/userinfo",
    )


#: Out-of-band redirect URI for desktop/CLI applications.
OOB_REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


def make_digest_auth(username: str, password: str) -> httpx.DigestAuth:
    """Create an httpx DigestAuth instance for MusicBrainz API authentication.

    Args:
        username: MusicBrainz username.
        password: MusicBrainz password.
    """
    return httpx.DigestAuth(username, password)


def generate_pkce() -> tuple[str, str]:
    """Generate a PKCE code verifier and S256 challenge pair.

    Returns:
        Tuple of ``(code_verifier, code_challenge)``.
    """
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def build_authorization_url(
    client_id: str,
    redirect_uri: str,
    scopes: list[str],
    *,
    state: str | None = None,
    code_challenge: str | None = None,
    access_type: str | None = None,
    server: str = DEFAULT_SERVER,
) -> str:
    """Build the OAuth2 authorization URL to redirect the user to.

    Args:
        client_id: OAuth2 client ID from your registered application.
        redirect_uri: Must match the registered redirect URI exactly.
        scopes: List of scopes (e.g. ``["tag", "rating", "collection"]``).
        state: Optional CSRF token / state string.
        code_challenge: Optional PKCE S256 challenge (from :func:`generate_pkce`).
        access_type: ``"offline"`` to get a refresh token, ``"online"`` (default) otherwise.
        server: Server base URL. Defaults to ``https://musicbrainz.org``.

    Returns:
        Full authorization URL to open in a browser.
    """
    authorize_url, _, _, _ = _oauth_urls(server)
    params: dict[str, str] = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
    }
    if state:
        params["state"] = state
    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"
    if access_type:
        params["access_type"] = access_type
    from urllib.parse import urlencode

    return f"{authorize_url}?{urlencode(params)}"


@dataclass
class OAuthToken:
    """An OAuth2 token pair with expiry tracking."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: str | None = None
    _obtained_at: float = field(default_factory=time.monotonic)

    @property
    def is_expired(self) -> bool:
        """Check if the access token has expired (with 60s safety margin)."""
        return time.monotonic() - self._obtained_at >= self.expires_in - 60

    @classmethod
    def from_response(cls, data: dict[str, str | int]) -> OAuthToken:
        """Create from a token endpoint JSON response."""
        return cls(
            access_token=str(data["access_token"]),
            token_type=str(data.get("token_type", "Bearer")),
            expires_in=int(data.get("expires_in", 3600)),
            refresh_token=str(data["refresh_token"]) if "refresh_token" in data else None,
        )


class OAuthHandler:
    """Manages the OAuth2 token lifecycle (exchange, refresh, revoke).

    Args:
        client_id: OAuth2 client ID.
        client_secret: OAuth2 client secret.
        redirect_uri: Registered redirect URI.
        server: Server base URL. Defaults to ``https://musicbrainz.org``.
    """

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, *, server: str = DEFAULT_SERVER) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._authorize_url, self._token_url, self._revoke_url, self._userinfo_url = _oauth_urls(server)
        self.token: OAuthToken | None = None

    async def exchange_code(
        self,
        code: str,
        *,
        code_verifier: str | None = None,
    ) -> OAuthToken:
        """Exchange an authorization code for an access token.

        Args:
            code: Authorization code from the callback.
            code_verifier: PKCE code verifier if PKCE was used.

        Returns:
            The obtained :class:`OAuthToken`.
        """
        data: dict[str, str] = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }
        if code_verifier:
            data["code_verifier"] = code_verifier
        self.token = await self._token_request(data)
        return self.token

    async def refresh(self) -> OAuthToken:
        """Refresh the access token using the stored refresh token.

        Returns:
            The new :class:`OAuthToken`.

        Raises:
            ValueError: If no refresh token is available.
        """
        if not self.token or not self.token.refresh_token:
            raise ValueError("No refresh token available. Re-authorize the application.")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.token.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        self.token = await self._token_request(data)
        return self.token

    async def revoke(self, token: str | None = None) -> None:
        """Revoke a token (access or refresh).

        Args:
            token: Token string to revoke. Defaults to the current refresh token,
                   or access token if no refresh token exists.
        """
        if token is None:
            if self.token and self.token.refresh_token:
                token = self.token.refresh_token
            elif self.token:
                token = self.token.access_token
            else:
                raise ValueError("No token to revoke.")
        async with httpx.AsyncClient() as client:
            await client.post(
                self._revoke_url,
                data={
                    "token": token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
        self.token = None

    async def get_access_token(self) -> str:
        """Get a valid access token, refreshing if expired.

        Returns:
            A valid access token string.

        Raises:
            ValueError: If no token is available.
        """
        if not self.token:
            raise ValueError("No token available. Call exchange_code() first.")
        if self.token.is_expired and self.token.refresh_token:
            await self.refresh()
        return self.token.access_token

    async def _token_request(self, data: dict[str, str]) -> OAuthToken:
        """Send a POST to the token endpoint and parse the response."""
        async with httpx.AsyncClient() as client:
            response = await client.post(self._token_url, data=data)
            response.raise_for_status()
            return OAuthToken.from_response(response.json())

    def set_token(self, access_token: str, refresh_token: str | None = None, expires_in: int = 3600) -> None:
        """Manually set a token (e.g. loaded from storage).

        Args:
            access_token: The access token string.
            refresh_token: Optional refresh token.
            expires_in: Token lifetime in seconds.
        """
        self.token = OAuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )
