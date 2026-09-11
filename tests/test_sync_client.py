"""Tests for the synchronous client wrapper."""

from __future__ import annotations

import httpx
import pytest
import respx

from musicbrainzpy.exceptions import AuthenticationError
from musicbrainzpy.models import Artist, Collection
from musicbrainzpy.sync_client import SyncMusicBrainzClient
from tests.conftest import (
    ARTIST_LOOKUP_RESPONSE,
    ARTIST_SEARCH_RESPONSE,
    COLLECTION_LIST_RESPONSE,
    URL_LOOKUP_WITH_RELS_RESPONSE,
)


class TestSyncClient:
    def test_lookup(self) -> None:
        with respx.mock(base_url="https://musicbrainz.org/ws/2") as mock_api:
            mbid = "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"
            mock_api.get(f"/artist/{mbid}", params={}).mock(
                return_value=httpx.Response(200, json=ARTIST_LOOKUP_RESPONSE)
            )
            with SyncMusicBrainzClient("test", "0.1", "test@example.com", rate_limit=0) as c:
                result = c.lookup("artist", mbid)
                assert result["name"] == "Metallica"

    def test_lookup_typed(self) -> None:
        with respx.mock(base_url="https://musicbrainz.org/ws/2") as mock_api:
            mbid = "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"
            mock_api.get(f"/artist/{mbid}", params={}).mock(
                return_value=httpx.Response(200, json=ARTIST_LOOKUP_RESPONSE)
            )
            with SyncMusicBrainzClient("test", "0.1", "test@example.com", rate_limit=0) as c:
                result = c.lookup_typed("artist", mbid)
                assert isinstance(result, Artist)
                assert result.name == "Metallica"

    def test_search_typed(self) -> None:
        with respx.mock(base_url="https://musicbrainz.org/ws/2") as mock_api:
            mock_api.get("/artist", params={"query": "Metallica", "limit": "25", "offset": "0"}).mock(
                return_value=httpx.Response(200, json=ARTIST_SEARCH_RESPONSE)
            )
            with SyncMusicBrainzClient("test", "0.1", "test@example.com", rate_limit=0) as c:
                result = c.search_typed("artist", "Metallica")
                assert result.count == 1
                assert isinstance(result.items[0], Artist)

    def test_lookup_by_url_with_includes(self) -> None:
        url = "https://open.spotify.com/artist/5YEPudiLsVYgkZmABzsttS"
        with respx.mock(base_url="https://musicbrainz.org/ws/2") as mock_api:
            mock_api.get("/url", params={"resource": url, "inc": "artist-rels"}).mock(
                return_value=httpx.Response(200, json=URL_LOOKUP_WITH_RELS_RESPONSE)
            )
            with SyncMusicBrainzClient("test", "0.1", "test@example.com", rate_limit=0) as c:
                result = c.lookup_by_url(url, includes=["artist-rels"])
                assert result["relations"][0]["artist"]["name"] == "Tajnic"

    def test_get_collections_with_auth(self) -> None:
        with respx.mock(base_url="https://musicbrainz.org/ws/2") as mock_api:
            mock_api.get("/collection").mock(return_value=httpx.Response(200, json=COLLECTION_LIST_RESPONSE))
            with SyncMusicBrainzClient(
                "test", "0.1", "test@example.com", rate_limit=0, username="user", password="pass"
            ) as c:
                result = c.get_collections()
                assert len(result) == 1
                assert isinstance(result[0], Collection)
                assert result[0].name == "My Releases"

    def test_get_collections_without_auth_raises(self) -> None:
        with (
            SyncMusicBrainzClient("test", "0.1", "test@example.com", rate_limit=0) as c,
            pytest.raises(AuthenticationError, match="Authentication required"),
        ):
            c.get_collections()
