"""Tests for OAuth2 authentication."""

from __future__ import annotations

import time

import httpx
import pytest
import respx

from musicbrainzpy.auth import (
    AUTHORIZE_URL,
    TOKEN_URL,
    OAuthHandler,
    OAuthToken,
    build_authorization_url,
    generate_pkce,
)

TOKEN_RESPONSE = {
    "access_token": "test-access-token",
    "expires_in": 3600,
    "token_type": "Bearer",
    "refresh_token": "test-refresh-token",
}


class TestGeneratePkce:
    def test_returns_verifier_and_challenge(self) -> None:
        verifier, challenge = generate_pkce()
        assert len(verifier) > 40
        assert len(challenge) > 20
        assert verifier != challenge

    def test_unique_each_call(self) -> None:
        v1, _ = generate_pkce()
        v2, _ = generate_pkce()
        assert v1 != v2


class TestBuildAuthorizationUrl:
    def test_basic_url(self) -> None:
        url = build_authorization_url("my-client-id", "http://localhost:8080", ["tag", "rating"])
        assert url.startswith(AUTHORIZE_URL)
        assert "client_id=" in url
        assert "scope=" in url
        assert "response_type=" in url

    def test_with_pkce_and_state(self) -> None:
        _, challenge = generate_pkce()
        url = build_authorization_url("cid", "http://localhost", ["profile"], state="csrf123", code_challenge=challenge)
        assert "code_challenge=" in url
        assert "code_challenge_method=S256" in url
        assert "state=" in url

    def test_with_offline_access(self) -> None:
        url = build_authorization_url("cid", "http://localhost", ["tag"], access_type="offline")
        assert "access_type=offline" in url

    def test_custom_server(self) -> None:
        url = build_authorization_url("cid", "http://localhost", ["tag"], server="https://test.musicbrainz.org")
        assert url.startswith("https://test.musicbrainz.org/oauth2/authorize?")


class TestOAuthToken:
    def test_from_response(self) -> None:
        token = OAuthToken.from_response(TOKEN_RESPONSE)
        assert token.access_token == "test-access-token"
        assert token.refresh_token == "test-refresh-token"
        assert token.expires_in == 3600
        assert token.token_type == "Bearer"

    def test_not_expired_initially(self) -> None:
        token = OAuthToken(access_token="tok", expires_in=3600)
        assert token.is_expired is False

    def test_expired(self) -> None:
        token = OAuthToken(access_token="tok", expires_in=3600, _obtained_at=time.monotonic() - 3600)
        assert token.is_expired is True

    def test_no_refresh_token(self) -> None:
        data = {"access_token": "tok", "expires_in": 3600, "token_type": "Bearer"}
        token = OAuthToken.from_response(data)
        assert token.refresh_token is None


class TestOAuthHandler:
    @pytest.fixture
    def handler(self) -> OAuthHandler:
        return OAuthHandler("client-id", "client-secret", "http://localhost:8080")

    async def test_exchange_code(self, handler: OAuthHandler) -> None:
        with respx.mock:
            respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKEN_RESPONSE))
            token = await handler.exchange_code("auth-code-123")
            assert token.access_token == "test-access-token"
            assert handler.token is token

    async def test_exchange_code_with_pkce(self, handler: OAuthHandler) -> None:
        with respx.mock:
            route = respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKEN_RESPONSE))
            await handler.exchange_code("auth-code-123", code_verifier="my-verifier")
            request = route.calls[0].request
            assert b"code_verifier=my-verifier" in request.content

    async def test_refresh(self, handler: OAuthHandler) -> None:
        handler.token = OAuthToken(access_token="old-token", refresh_token="refresh-tok", expires_in=0, _obtained_at=0)
        with respx.mock:
            respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKEN_RESPONSE))
            new_token = await handler.refresh()
            assert new_token.access_token == "test-access-token"

    async def test_refresh_without_token_raises(self, handler: OAuthHandler) -> None:
        with pytest.raises(ValueError, match="No refresh token"):
            await handler.refresh()

    async def test_get_access_token_refreshes_if_expired(self, handler: OAuthHandler) -> None:
        handler.token = OAuthToken(
            access_token="expired-tok", refresh_token="refresh-tok", expires_in=0, _obtained_at=0
        )
        with respx.mock:
            respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKEN_RESPONSE))
            token = await handler.get_access_token()
            assert token == "test-access-token"

    async def test_get_access_token_without_token_raises(self, handler: OAuthHandler) -> None:
        with pytest.raises(ValueError, match="No token available"):
            await handler.get_access_token()

    def test_set_token(self, handler: OAuthHandler) -> None:
        handler.set_token("my-token", refresh_token="my-refresh", expires_in=7200)
        assert handler.token is not None
        assert handler.token.access_token == "my-token"
        assert handler.token.refresh_token == "my-refresh"
        assert handler.token.expires_in == 7200

    async def test_revoke(self, handler: OAuthHandler) -> None:
        handler.token = OAuthToken(access_token="tok", refresh_token="refresh-tok")
        with respx.mock:
            route = respx.post("https://musicbrainz.org/oauth2/revoke").mock(return_value=httpx.Response(200))
            await handler.revoke()
            assert handler.token is None
            request = route.calls[0].request
            assert b"token=refresh-tok" in request.content

    async def test_revoke_without_token_raises(self, handler: OAuthHandler) -> None:
        with pytest.raises(ValueError, match="No token to revoke"):
            await handler.revoke()

    async def test_custom_server(self) -> None:
        h = OAuthHandler("cid", "csecret", "http://localhost", server="https://test.musicbrainz.org")
        with respx.mock:
            route = respx.post("https://test.musicbrainz.org/oauth2/token").mock(
                return_value=httpx.Response(200, json=TOKEN_RESPONSE)
            )
            token = await h.exchange_code("code-123")
            assert token.access_token == "test-access-token"
            assert route.called
