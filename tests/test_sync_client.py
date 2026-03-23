"""Tests for the synchronous client wrapper."""

from __future__ import annotations

import httpx
import respx

from musicbrainzpy.models import Artist
from musicbrainzpy.sync_client import SyncMusicBrainzClient
from tests.conftest import ARTIST_LOOKUP_RESPONSE, ARTIST_SEARCH_RESPONSE


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
