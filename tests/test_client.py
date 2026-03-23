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
from musicbrainzpy.models import Artist, Release
from tests.conftest import (
    ARTIST_LOOKUP_RESPONSE,
    ARTIST_SEARCH_RESPONSE,
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
        mock_api.get(f"/artist/{mbid}", params={"fmt": "json"}).mock(
            return_value=httpx.Response(200, json=ARTIST_LOOKUP_RESPONSE)
        )
        result = await client.lookup("artist", mbid)
        assert result["name"] == "Metallica"
        assert result["id"] == mbid

    async def test_lookup_with_includes(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mbid = "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"
        mock_api.get(f"/artist/{mbid}", params={"fmt": "json", "inc": "releases+tags"}).mock(
            return_value=httpx.Response(200, json=ARTIST_LOOKUP_RESPONSE)
        )
        result = await client.lookup("artist", mbid, includes=["releases", "tags"])
        assert result["name"] == "Metallica"

    async def test_lookup_not_found(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mbid = "00000000-0000-0000-0000-000000000000"
        mock_api.get(f"/artist/{mbid}", params={"fmt": "json"}).mock(return_value=httpx.Response(404, text="Not Found"))
        with pytest.raises(NotFoundError):
            await client.lookup("artist", mbid)


class TestSearch:
    async def test_search_artists(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mock_api.get("/artist", params={"fmt": "json", "query": "Metallica", "limit": "25", "offset": "0"}).mock(
            return_value=httpx.Response(200, json=ARTIST_SEARCH_RESPONSE)
        )
        result = await client.search("artist", "Metallica")
        assert result["count"] == 1
        assert result["artists"][0]["name"] == "Metallica"

    async def test_search_with_paging(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mock_api.get("/artist", params={"fmt": "json", "query": "rock", "limit": "10", "offset": "5"}).mock(
            return_value=httpx.Response(200, json=ARTIST_SEARCH_RESPONSE)
        )
        result = await client.search("artist", "rock", limit=10, offset=5)
        assert result["count"] == 1


class TestBrowse:
    async def test_browse_releases(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        artist_id = "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"
        mock_api.get(
            "/release",
            params={"fmt": "json", "artist": artist_id, "limit": "25", "offset": "0"},
        ).mock(return_value=httpx.Response(200, json=RELEASE_BROWSE_RESPONSE))
        result = await client.browse("release", linked_type="artist", linked_id=artist_id)
        assert result["release-count"] == 1
        assert result["releases"][0]["title"] == "Master of Puppets"

    async def test_browse_with_includes(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        artist_id = "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"
        mock_api.get(
            "/release",
            params={"fmt": "json", "artist": artist_id, "limit": "10", "offset": "0", "inc": "labels"},
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
        mock_api.get(f"/artist/{mbid}", params={"fmt": "json"}).mock(
            return_value=httpx.Response(200, json=ARTIST_LOOKUP_RESPONSE)
        )
        result = await client.lookup_typed("artist", mbid)
        assert isinstance(result, Artist)
        assert result.name == "Metallica"


class TestSearchTyped:
    async def test_returns_search_result(self, client: MusicBrainzClient, mock_api: respx.MockRouter) -> None:
        mock_api.get("/artist", params={"fmt": "json", "query": "Metallica", "limit": "25", "offset": "0"}).mock(
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
            params={"fmt": "json", "artist": artist_id, "limit": "25", "offset": "0"},
        ).mock(return_value=httpx.Response(200, json=RELEASE_BROWSE_RESPONSE))
        result = await client.browse_typed("release", linked_type="artist", linked_id=artist_id)
        assert isinstance(result, BrowseResult)
        assert result.count == 1
        assert len(result.items) == 1
        assert isinstance(result.items[0], Release)
        assert result.items[0].title == "Master of Puppets"
