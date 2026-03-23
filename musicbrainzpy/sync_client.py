"""Synchronous wrapper around the async MusicBrainz client."""

from __future__ import annotations

import asyncio
from typing import Any

from musicbrainzpy.client import BrowseResult, MusicBrainzClient, SearchResult
from musicbrainzpy.models import MBModel, Recording, Release, Work


class SyncMusicBrainzClient:
    """Synchronous client for the MusicBrainz JSON API.

    Thin wrapper that runs the async client via ``asyncio.run()``.
    Accepts the same constructor arguments as :class:`MusicBrainzClient`.
    """

    def __init__(
        self,
        app_name: str,
        app_version: str,
        app_contact: str,
        **kwargs: Any,
    ) -> None:
        self._async_client = MusicBrainzClient(app_name, app_version, app_contact, **kwargs)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        asyncio.run(self._async_client.close())

    def __enter__(self) -> SyncMusicBrainzClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _run(self, coro):  # noqa: ANN001, ANN202
        return asyncio.run(coro)

    # --- Raw methods ---

    def lookup(self, entity_type: str, mbid: str, includes: list[str] | None = None) -> dict[str, Any]:
        """Look up a single entity by MBID. See :meth:`MusicBrainzClient.lookup`."""
        return self._run(self._async_client.lookup(entity_type, mbid, includes))

    def browse(self, entity_type: str, **kwargs: Any) -> dict[str, Any]:
        """Browse entities. See :meth:`MusicBrainzClient.browse`."""
        return self._run(self._async_client.browse(entity_type, **kwargs))

    def search(self, entity_type: str, query: str, **kwargs: Any) -> dict[str, Any]:
        """Search for entities. See :meth:`MusicBrainzClient.search`."""
        return self._run(self._async_client.search(entity_type, query, **kwargs))

    # --- Typed methods ---

    def lookup_typed(self, entity_type: str, mbid: str, includes: list[str] | None = None) -> MBModel:
        """Look up an entity and return a typed model. See :meth:`MusicBrainzClient.lookup_typed`."""
        return self._run(self._async_client.lookup_typed(entity_type, mbid, includes))

    def search_typed(self, entity_type: str, query: str, **kwargs: Any) -> SearchResult[MBModel]:
        """Search and return typed models. See :meth:`MusicBrainzClient.search_typed`."""
        return self._run(self._async_client.search_typed(entity_type, query, **kwargs))

    def browse_typed(self, entity_type: str, **kwargs: Any) -> BrowseResult[MBModel]:
        """Browse and return typed models. See :meth:`MusicBrainzClient.browse_typed`."""
        return self._run(self._async_client.browse_typed(entity_type, **kwargs))

    # --- Non-MBID lookups ---

    def lookup_by_isrc(self, isrc: str, includes: list[str] | None = None) -> list[Recording]:
        """Look up recordings by ISRC. See :meth:`MusicBrainzClient.lookup_by_isrc`."""
        return self._run(self._async_client.lookup_by_isrc(isrc, includes))

    def lookup_by_iswc(self, iswc: str, includes: list[str] | None = None) -> list[Work]:
        """Look up works by ISWC. See :meth:`MusicBrainzClient.lookup_by_iswc`."""
        return self._run(self._async_client.lookup_by_iswc(iswc, includes))

    def lookup_by_discid(self, discid: str, **kwargs: Any) -> list[Release]:
        """Look up releases by disc ID. See :meth:`MusicBrainzClient.lookup_by_discid`."""
        return self._run(self._async_client.lookup_by_discid(discid, **kwargs))

    def lookup_by_url(self, *urls: str) -> dict[str, Any]:
        """Look up URL entities. See :meth:`MusicBrainzClient.lookup_by_url`."""
        return self._run(self._async_client.lookup_by_url(*urls))

    # --- Submissions ---

    def submit_tags(self, client_id: str, entities: dict[str, dict[str, list[str]]]) -> None:
        """Submit tags. See :meth:`MusicBrainzClient.submit_tags`."""
        self._run(self._async_client.submit_tags(client_id, entities))

    def submit_ratings(self, client_id: str, entities: dict[str, dict[str, int]]) -> None:
        """Submit ratings. See :meth:`MusicBrainzClient.submit_ratings`."""
        self._run(self._async_client.submit_ratings(client_id, entities))

    def submit_barcodes(self, client_id: str, barcodes: dict[str, str]) -> None:
        """Submit barcodes. See :meth:`MusicBrainzClient.submit_barcodes`."""
        self._run(self._async_client.submit_barcodes(client_id, barcodes))

    def submit_isrcs(self, client_id: str, isrcs: dict[str, list[str]]) -> None:
        """Submit ISRCs. See :meth:`MusicBrainzClient.submit_isrcs`."""
        self._run(self._async_client.submit_isrcs(client_id, isrcs))

    def collection_add(self, client_id: str, collection_id: str, entity_type: str, mbids: list[str]) -> None:
        """Add to collection. See :meth:`MusicBrainzClient.collection_add`."""
        self._run(self._async_client.collection_add(client_id, collection_id, entity_type, mbids))

    def collection_remove(self, client_id: str, collection_id: str, entity_type: str, mbids: list[str]) -> None:
        """Remove from collection. See :meth:`MusicBrainzClient.collection_remove`."""
        self._run(self._async_client.collection_remove(client_id, collection_id, entity_type, mbids))
