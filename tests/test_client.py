"""Tests for the MusicBrainz API client."""

from __future__ import annotations

import httpx
import pytest
import respx

from musicbrainzpy.client import (
    BrowseResult,
    MusicBrainzClient,
    SearchResult,
    _build_user_agent,
    _get_entity_info,
    _raise_for_status,
)
from musicbrainzpy.exceptions import (
    AuthenticationError,
    InvalidRequestError,
    MusicBrainzError,
    NotFoundError,
    RateLimitedError,
)
from musicbrainzpy.models import Artist, Recording, Release, Work
from tests.conftest import (
    ARTIST_LOOKUP_RESPONSE,
    ARTIST_SEARCH_RESPONSE,
    DISCID_LOOKUP_RESPONSE,
    ISRC_LOOKUP_RESPONSE,
    ISWC_LOOKUP_RESPONSE,
    RELEASE_BROWSE_RESPONSE,
)

# --- Helper tests ---


class TestBuildUserAgent:
    def test_format(self) -> None:
        result = _build_user_agent("MyApp", "1.0", "me@example.com")
        assert result == "MyApp/1.0 ( me@example.com )"


class TestRaiseForStatus:
    def test_success_does_nothing(self) -> None:
        response = httpx.Response(200)
        _raise_for_status(response)  # should not raise

    @pytest.mark.parametrize(
        ("status", "exc_class"),
        [
            (400, InvalidRequestError),
            (401, AuthenticationError),
            (404, NotFoundError),
            (503, RateLimitedError),
        ],
    )
    def test_known_errors(self, status: int, exc_class: type[MusicBrainzError]) -> None:
        response = httpx.Response(status, text="error")
        with pytest.raises(exc_class, match=f"HTTP {status}"):
            _raise_for_status(response)

    def test_unknown_error(self) -> None:
        response = httpx.Response(500, text="server error")
        with pytest.raises(MusicBrainzError, match="HTTP 500"):
            _raise_for_status(response)


# --- Client tests ---


class TestClientInit:
    def test_user_agent_header(self, client: MusicBrainzClient) -> None:
        ua = client._client.headers["user-agent"]
        assert ua == "test-app/0.1.0 ( test@example.com )"

    def test_accept_header(self, client: MusicBrainzClient) -> None:
        assert client._client.headers["accept"] == "application/json"

    def test_base_url_trailing_slash(self) -> None:
        c = MusicBrainzClient("a", "1", "x", base_url="https://example.com/ws/2", rate_limit=0)
        assert c._base_url == "https://example.com/ws/2/"

    def test_base_url_keeps_trailing_slash(self) -> None:
        c = MusicBrainzClient("a", "1", "x", base_url="https://example.com/ws/2/", rate_limit=0)
        assert c._base_url == "https://example.com/ws/2/"

    async def test_context_manager(self) -> None:
        async with MusicBrainzClient("a", "1", "x", rate_limit=0) as c:
            assert c._client.is_closed is False
        assert c._client.is_closed is True


class TestLookup:
    async def test_lookup_artist(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mbid = "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"
        mock_api.get(f"/artist/{mbid}", params={}).mock(return_value=httpx.Response(200, json=ARTIST_LOOKUP_RESPONSE))
        result = await client.lookup("artist", mbid)
        assert result["name"] == "Metallica"
        assert result["id"] == mbid

    async def test_lookup_with_includes(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mbid = "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"
        mock_api.get(f"/artist/{mbid}", params={"inc": "releases+tags"}).mock(
            return_value=httpx.Response(200, json=ARTIST_LOOKUP_RESPONSE)
        )
        result = await client.lookup("artist", mbid, includes=["releases", "tags"])
        assert result["name"] == "Metallica"

    async def test_lookup_not_found(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mbid = "00000000-0000-0000-0000-000000000000"
        mock_api.get(f"/artist/{mbid}", params={}).mock(return_value=httpx.Response(404, text="Not Found"))
        with pytest.raises(NotFoundError):
            await client.lookup("artist", mbid)


class TestSearch:
    async def test_search_artists(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mock_api.get("/artist", params={"query": "Metallica", "limit": "25", "offset": "0"}).mock(
            return_value=httpx.Response(200, json=ARTIST_SEARCH_RESPONSE)
        )
        result = await client.search("artist", "Metallica")
        assert result["count"] == 1
        assert result["artists"][0]["name"] == "Metallica"

    async def test_search_with_paging(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mock_api.get("/artist", params={"query": "rock", "limit": "10", "offset": "5"}).mock(
            return_value=httpx.Response(200, json=ARTIST_SEARCH_RESPONSE)
        )
        result = await client.search("artist", "rock", limit=10, offset=5)
        assert result["count"] == 1


class TestBrowse:
    async def test_browse_releases(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        artist_id = "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"
        mock_api.get(
            "/release",
            params={"artist": artist_id, "limit": "25", "offset": "0"},
        ).mock(return_value=httpx.Response(200, json=RELEASE_BROWSE_RESPONSE))
        result = await client.browse("release", linked_type="artist", linked_id=artist_id)
        assert result["release-count"] == 1
        assert result["releases"][0]["title"] == "Master of Puppets"

    async def test_browse_with_includes(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        artist_id = "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"
        mock_api.get(
            "/release",
            params={"artist": artist_id, "limit": "10", "offset": "0", "inc": "labels"},
        ).mock(return_value=httpx.Response(200, json=RELEASE_BROWSE_RESPONSE))
        result = await client.browse(
            "release", linked_type="artist", linked_id=artist_id, limit=10, includes=["labels"]
        )
        assert result["releases"][0]["title"] == "Master of Puppets"


class TestGetEntityInfo:
    def test_known_type(self) -> None:
        model_class, list_key = _get_entity_info("artist")
        assert model_class is Artist
        assert list_key == "artists"

    def test_unknown_type(self) -> None:
        with pytest.raises(ValueError, match="Unknown entity type"):
            _get_entity_info("nonexistent")


class TestLookupTyped:
    async def test_returns_model(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mbid = "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"
        mock_api.get(f"/artist/{mbid}", params={}).mock(return_value=httpx.Response(200, json=ARTIST_LOOKUP_RESPONSE))
        result = await client.lookup_typed("artist", mbid)
        assert isinstance(result, Artist)
        assert result.name == "Metallica"


class TestSearchTyped:
    async def test_returns_search_result(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mock_api.get("/artist", params={"query": "Metallica", "limit": "25", "offset": "0"}).mock(
            return_value=httpx.Response(200, json=ARTIST_SEARCH_RESPONSE)
        )
        result = await client.search_typed("artist", "Metallica")
        assert isinstance(result, SearchResult)
        assert result.count == 1
        assert result.offset == 0
        assert len(result.items) == 1
        assert isinstance(result.items[0], Artist)
        assert result.items[0].name == "Metallica"


class TestBrowseTyped:
    async def test_returns_browse_result(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        artist_id = "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"
        mock_api.get(
            "/release",
            params={"artist": artist_id, "limit": "25", "offset": "0"},
        ).mock(return_value=httpx.Response(200, json=RELEASE_BROWSE_RESPONSE))
        result = await client.browse_typed("release", linked_type="artist", linked_id=artist_id)
        assert isinstance(result, BrowseResult)
        assert result.count == 1
        assert len(result.items) == 1
        assert isinstance(result.items[0], Release)
        assert result.items[0].title == "Master of Puppets"


class TestLookupByIsrc:
    async def test_returns_recordings(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mock_api.get("/isrc/USEE10100063", params={}).mock(return_value=httpx.Response(200, json=ISRC_LOOKUP_RESPONSE))
        results = await client.lookup_by_isrc("USEE10100063")
        assert len(results) == 1
        assert isinstance(results[0], Recording)
        assert results[0].title == "Enter Sandman"


class TestLookupByIswc:
    async def test_returns_works(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mock_api.get("/iswc/T-070.116.274-5", params={}).mock(
            return_value=httpx.Response(200, json=ISWC_LOOKUP_RESPONSE)
        )
        results = await client.lookup_by_iswc("T-070.116.274-5")
        assert len(results) == 1
        assert isinstance(results[0], Work)
        assert results[0].title == "Enter Sandman"


class TestLookupByDiscid:
    async def test_returns_releases(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        discid = "I5l9cCSFccLKFEKS.7wqSZAorPU-"
        mock_api.get(f"/discid/{discid}", params={}).mock(return_value=httpx.Response(200, json=DISCID_LOOKUP_RESPONSE))
        results = await client.lookup_by_discid(discid)
        assert len(results) == 1
        assert isinstance(results[0], Release)
        assert results[0].title == "Metallica"

    async def test_with_toc(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mock_api.get("/discid/-", params={"toc": "1+12+267257+150", "cdstubs": "no"}).mock(
            return_value=httpx.Response(200, json=DISCID_LOOKUP_RESPONSE)
        )
        results = await client.lookup_by_discid("-", toc="1+12+267257+150", cdstubs=False)
        assert len(results) == 1


class TestAuth:
    def test_no_auth_by_default(self, client: MusicBrainzClient) -> None:
        assert client.is_authenticated is False

    def test_digest_auth_with_credentials(self) -> None:
        c = MusicBrainzClient("a", "1", "x", rate_limit=0, username="user", password="pass")
        assert c.is_authenticated is True
        assert c._digest_auth is not None

    def test_oauth_auth(self) -> None:
        from musicbrainzpy.auth import OAuthHandler

        handler = OAuthHandler("cid", "csecret", "http://localhost")
        c = MusicBrainzClient("a", "1", "x", rate_limit=0, oauth=handler)
        assert c.is_authenticated is True
        assert c._oauth is handler

    async def test_post_without_auth_raises(self, client: MusicBrainzClient) -> None:
        with pytest.raises(AuthenticationError, match="Authentication required"):
            await client._post("tag", params={"client": "test-0.1"}, body="<xml/>")

    async def test_put_without_auth_raises(self, client: MusicBrainzClient) -> None:
        with pytest.raises(AuthenticationError, match="Authentication required"):
            await client._put("collection/abc/releases/def", params={"client": "test-0.1"})

    async def test_delete_without_auth_raises(self, client: MusicBrainzClient) -> None:
        with pytest.raises(AuthenticationError, match="Authentication required"):
            await client._delete("collection/abc/releases/def", params={"client": "test-0.1"})
