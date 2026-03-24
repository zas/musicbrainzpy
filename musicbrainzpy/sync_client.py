"""Synchronous MusicBrainz client using httpx.Client and SyncRateLimiter."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from musicbrainzpy._ratelimit import SyncRateLimiter
from musicbrainzpy._retry import DEFAULT_BASE_DELAY, DEFAULT_MAX_RETRIES, sync_retry
from musicbrainzpy.auth import make_digest_auth
from musicbrainzpy.client import (
    DEFAULT_BASE_URL,
    BrowseResult,
    SearchResult,
    _build_user_agent,
    _get_entity_info,
    _raise_for_status,
)
from musicbrainzpy.exceptions import AuthenticationError
from musicbrainzpy.models import Collection, MBModel, Recording, Release, Work


class SyncMusicBrainzClient:
    """Synchronous client for the MusicBrainz JSON API.

    Uses ``httpx.Client`` directly with a :class:`SyncRateLimiter` to enforce
    rate limiting across calls. Accepts the same constructor arguments as
    :class:`~musicbrainzpy.client.MusicBrainzClient`.
    """

    def __init__(
        self,
        app_name: str,
        app_version: str,
        app_contact: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        rate_limit: float = 1.0,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_base_delay: float = DEFAULT_BASE_DELAY,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/") + "/"
        self._rate_limiter = SyncRateLimiter(interval=rate_limit)
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._digest_auth = make_digest_auth(username, password) if username and password else None
        self._client = httpx.Client(
            headers={
                "User-Agent": _build_user_agent(app_name, app_version, app_contact),
                "Accept": "application/json",
            },
            follow_redirects=True,
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> SyncMusicBrainzClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _get(self, path: str, params: Mapping[str, str | list[str]] | None = None) -> dict[str, Any]:
        """Perform a rate-limited GET request and return parsed JSON."""

        def _do() -> dict[str, Any]:
            self._rate_limiter.acquire()
            url = self._base_url + path
            auth = self._digest_auth if self._digest_auth else None
            response = self._client.get(url, params=params, auth=auth)
            _raise_for_status(response)
            return response.json()

        return sync_retry(_do, max_retries=self._max_retries, base_delay=self._retry_base_delay)

    def _get_authenticated(self, path: str, params: Mapping[str, str | list[str]] | None = None) -> dict[str, Any]:
        """Perform a rate-limited authenticated GET request.

        Raises:
            AuthenticationError: If no credentials were configured.
        """
        if not self._digest_auth:
            raise AuthenticationError("Authentication required. Provide username/password.")

        def _do() -> dict[str, Any]:
            self._rate_limiter.acquire()
            url = self._base_url + path
            response = self._client.get(url, params=params, auth=self._digest_auth)
            _raise_for_status(response)
            return response.json()

        return sync_retry(_do, max_retries=self._max_retries, base_delay=self._retry_base_delay)

    # --- Raw methods ---

    def lookup(self, entity_type: str, mbid: str, includes: list[str] | None = None) -> dict[str, Any]:
        """Look up a single entity by MBID. See :meth:`MusicBrainzClient.lookup`."""
        params: dict[str, str] = {}
        if includes:
            params["inc"] = "+".join(includes)
        return self._get(f"{entity_type}/{mbid}", params)

    def browse(
        self,
        entity_type: str,
        *,
        linked_type: str,
        linked_id: str,
        limit: int = 25,
        offset: int = 0,
        includes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Browse entities. See :meth:`MusicBrainzClient.browse`."""
        params: dict[str, str] = {
            linked_type: linked_id,
            "limit": str(limit),
            "offset": str(offset),
        }
        if includes:
            params["inc"] = "+".join(includes)
        return self._get(entity_type, params)

    def search(self, entity_type: str, query: str, *, limit: int = 25, offset: int = 0) -> dict[str, Any]:
        """Search for entities. See :meth:`MusicBrainzClient.search`."""
        params: dict[str, str] = {
            "query": query,
            "limit": str(limit),
            "offset": str(offset),
        }
        return self._get(entity_type, params)

    # --- Typed methods ---

    def lookup_typed(self, entity_type: str, mbid: str, includes: list[str] | None = None) -> MBModel:
        """Look up an entity and return a typed model. See :meth:`MusicBrainzClient.lookup_typed`."""
        model_class, _ = _get_entity_info(entity_type)
        data = self.lookup(entity_type, mbid, includes)
        return model_class.model_validate(data)

    def search_typed(self, entity_type: str, query: str, *, limit: int = 25, offset: int = 0) -> SearchResult[MBModel]:
        """Search and return typed models. See :meth:`MusicBrainzClient.search_typed`."""
        model_class, list_key = _get_entity_info(entity_type)
        data = self.search(entity_type, query, limit=limit, offset=offset)
        items = [model_class.model_validate(item) for item in data.get(list_key, [])]
        return SearchResult(items=items, count=data.get("count", 0), offset=data.get("offset", 0))

    def browse_typed(
        self,
        entity_type: str,
        *,
        linked_type: str,
        linked_id: str,
        limit: int = 25,
        offset: int = 0,
        includes: list[str] | None = None,
    ) -> BrowseResult[MBModel]:
        """Browse and return typed models. See :meth:`MusicBrainzClient.browse_typed`."""
        model_class, list_key = _get_entity_info(entity_type)
        data = self.browse(
            entity_type, linked_type=linked_type, linked_id=linked_id, limit=limit, offset=offset, includes=includes
        )
        items = [model_class.model_validate(item) for item in data.get(list_key, [])]
        singular = entity_type
        return BrowseResult(
            items=items,
            count=data.get(f"{singular}-count", 0),
            offset=data.get(f"{singular}-offset", 0),
        )

    # --- Non-MBID lookups ---

    def lookup_by_isrc(self, isrc: str, includes: list[str] | None = None) -> list[Recording]:
        """Look up recordings by ISRC. See :meth:`MusicBrainzClient.lookup_by_isrc`."""
        params: dict[str, str] = {}
        if includes:
            params["inc"] = "+".join(includes)
        data = self._get(f"isrc/{isrc}", params)
        return [Recording.model_validate(r) for r in data.get("recordings", [])]

    def lookup_by_iswc(self, iswc: str, includes: list[str] | None = None) -> list[Work]:
        """Look up works by ISWC. See :meth:`MusicBrainzClient.lookup_by_iswc`."""
        params: dict[str, str] = {}
        if includes:
            params["inc"] = "+".join(includes)
        data = self._get(f"iswc/{iswc}", params)
        return [Work.model_validate(w) for w in data.get("works", [])]

    def lookup_by_discid(
        self,
        discid: str,
        *,
        toc: str | None = None,
        cdstubs: bool = True,
        media_format: str | None = None,
        includes: list[str] | None = None,
    ) -> list[Release]:
        """Look up releases by disc ID. See :meth:`MusicBrainzClient.lookup_by_discid`."""
        params: dict[str, str] = {}
        if toc:
            params["toc"] = toc
        if not cdstubs:
            params["cdstubs"] = "no"
        if media_format:
            params["media-format"] = media_format
        if includes:
            params["inc"] = "+".join(includes)
        data = self._get(f"discid/{discid}", params)
        return [Release.model_validate(r) for r in data.get("releases", [])]

    def lookup_by_url(self, *urls: str) -> dict[str, Any]:
        """Look up URL entities. See :meth:`MusicBrainzClient.lookup_by_url`."""
        params: dict[str, str | list[str]] = {"resource": list(urls)} if len(urls) > 1 else {"resource": urls[0]}
        return self._get("url", params)

    # --- Collections ---

    def get_collections(self) -> list[Collection]:
        """List the authenticated user's collections. See :meth:`MusicBrainzClient.get_collections`."""
        data = self._get_authenticated("collection")
        return [Collection.model_validate(c) for c in data.get("collections", [])]
