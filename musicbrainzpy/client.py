"""MusicBrainz API client.

Async-first HTTP client for the MusicBrainz JSON API.
Handles rate limiting, User-Agent, and error mapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from musicbrainzpy._ratelimit import RateLimiter
from musicbrainzpy.exceptions import (
    AuthenticationError,
    InvalidRequestError,
    MusicBrainzError,
    NotFoundError,
    RateLimitedError,
)
from musicbrainzpy.models import (
    Area,
    Artist,
    Event,
    GenreFull,
    Instrument,
    Label,
    MBModel,
    Place,
    Recording,
    Release,
    ReleaseGroup,
    Series,
    Url,
    Work,
)

DEFAULT_BASE_URL = "https://musicbrainz.org/ws/2/"

#: Maps HTTP status codes to exception classes.
_STATUS_EXCEPTIONS: dict[int, type[MusicBrainzError]] = {
    400: InvalidRequestError,
    401: AuthenticationError,
    404: NotFoundError,
    503: RateLimitedError,
}

#: Maps entity type strings to (model_class, list_key_in_json).
#: Search responses use the list key directly; browse uses it with -count/-offset suffixes.
_ENTITY_MAP: dict[str, tuple[type[MBModel], str]] = {
    "area": (Area, "areas"),
    "artist": (Artist, "artists"),
    "event": (Event, "events"),
    "genre": (GenreFull, "genres"),
    "instrument": (Instrument, "instruments"),
    "label": (Label, "labels"),
    "place": (Place, "places"),
    "recording": (Recording, "recordings"),
    "release": (Release, "releases"),
    "release-group": (ReleaseGroup, "release-groups"),
    "series": (Series, "series"),
    "url": (Url, "urls"),
    "work": (Work, "works"),
}


def _build_user_agent(app_name: str, app_version: str, app_contact: str) -> str:
    """Build a User-Agent string per MusicBrainz requirements.

    Format: ``AppName/Version ( contact-url-or-email )``
    """
    return f"{app_name}/{app_version} ( {app_contact} )"


def _raise_for_status(response: httpx.Response) -> None:
    """Raise a typed exception for non-2xx responses."""
    if response.is_success:
        return
    exc_class = _STATUS_EXCEPTIONS.get(response.status_code, MusicBrainzError)
    raise exc_class(f"HTTP {response.status_code}: {response.text}")


def _get_entity_info(entity_type: str) -> tuple[type[MBModel], str]:
    """Look up model class and JSON list key for an entity type."""
    try:
        return _ENTITY_MAP[entity_type]
    except KeyError:
        raise ValueError(f"Unknown entity type: {entity_type!r}") from None


@dataclass
class SearchResult[T: MBModel]:
    """Wrapper for search responses."""

    items: list[T]
    count: int
    offset: int


@dataclass
class BrowseResult[T: MBModel]:
    """Wrapper for browse responses."""

    items: list[T]
    count: int
    offset: int


class MusicBrainzClient:
    """Async client for the MusicBrainz JSON API.

    Args:
        app_name: Application name for User-Agent.
        app_version: Application version for User-Agent.
        app_contact: Contact URL or email for User-Agent.
        base_url: API base URL. Defaults to the official endpoint.
        rate_limit: Minimum seconds between requests. Set to 0 to disable.
    """

    def __init__(
        self,
        app_name: str,
        app_version: str,
        app_contact: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        rate_limit: float = 1.0,
    ) -> None:
        self._base_url = base_url.rstrip("/") + "/"
        self._rate_limiter = RateLimiter(interval=rate_limit)
        self._client = httpx.AsyncClient(
            headers={
                "User-Agent": _build_user_agent(app_name, app_version, app_contact),
                "Accept": "application/json",
            },
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> MusicBrainzClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    # --- Raw methods (return dicts) ---

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Perform a rate-limited GET request and return parsed JSON."""
        await self._rate_limiter.acquire()
        url = self._base_url + path
        all_params = {"fmt": "json"}
        if params:
            all_params.update(params)
        response = await self._client.get(url, params=all_params)
        _raise_for_status(response)
        return response.json()

    async def lookup(self, entity_type: str, mbid: str, includes: list[str] | None = None) -> dict[str, Any]:
        """Look up a single entity by MBID.

        Args:
            entity_type: Entity type (e.g. ``"artist"``, ``"release-group"``).
            mbid: The MusicBrainz ID.
            includes: Optional ``inc=`` subqueries (e.g. ``["releases", "tags"]``).
        """
        params: dict[str, str] = {}
        if includes:
            params["inc"] = "+".join(includes)
        return await self._get(f"{entity_type}/{mbid}", params)

    async def browse(
        self,
        entity_type: str,
        *,
        linked_type: str,
        linked_id: str,
        limit: int = 25,
        offset: int = 0,
        includes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Browse entities linked to another entity.

        Args:
            entity_type: What to list (e.g. ``"release"``).
            linked_type: The entity you're browsing by (e.g. ``"artist"``).
            linked_id: MBID of the linked entity.
            limit: Results per page (max 100).
            offset: Paging offset.
            includes: Optional ``inc=`` subqueries.
        """
        params: dict[str, str] = {
            linked_type: linked_id,
            "limit": str(limit),
            "offset": str(offset),
        }
        if includes:
            params["inc"] = "+".join(includes)
        return await self._get(entity_type, params)

    async def search(
        self,
        entity_type: str,
        query: str,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search for entities matching a Lucene query.

        Args:
            entity_type: Entity type to search (e.g. ``"artist"``).
            query: Lucene query string.
            limit: Results per page (max 100).
            offset: Paging offset.
        """
        params: dict[str, str] = {
            "query": query,
            "limit": str(limit),
            "offset": str(offset),
        }
        return await self._get(entity_type, params)

    # --- Typed methods ---

    async def lookup_typed(self, entity_type: str, mbid: str, includes: list[str] | None = None) -> MBModel:
        """Look up an entity by MBID and return a typed model.

        Args:
            entity_type: Entity type (e.g. ``"artist"``, ``"release-group"``).
            mbid: The MusicBrainz ID.
            includes: Optional ``inc=`` subqueries.
        """
        model_class, _ = _get_entity_info(entity_type)
        data = await self.lookup(entity_type, mbid, includes)
        return model_class.model_validate(data)

    async def search_typed(
        self,
        entity_type: str,
        query: str,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> SearchResult[MBModel]:
        """Search for entities and return typed models.

        Args:
            entity_type: Entity type to search.
            query: Lucene query string.
            limit: Results per page (max 100).
            offset: Paging offset.
        """
        model_class, list_key = _get_entity_info(entity_type)
        data = await self.search(entity_type, query, limit=limit, offset=offset)
        items = [model_class.model_validate(item) for item in data.get(list_key, [])]
        return SearchResult(items=items, count=data.get("count", 0), offset=data.get("offset", 0))

    async def browse_typed(
        self,
        entity_type: str,
        *,
        linked_type: str,
        linked_id: str,
        limit: int = 25,
        offset: int = 0,
        includes: list[str] | None = None,
    ) -> BrowseResult[MBModel]:
        """Browse linked entities and return typed models.

        Args:
            entity_type: What to list (e.g. ``"release"``).
            linked_type: The entity you're browsing by (e.g. ``"artist"``).
            linked_id: MBID of the linked entity.
            limit: Results per page (max 100).
            offset: Paging offset.
            includes: Optional ``inc=`` subqueries.
        """
        model_class, list_key = _get_entity_info(entity_type)
        data = await self.browse(
            entity_type, linked_type=linked_type, linked_id=linked_id, limit=limit, offset=offset, includes=includes
        )
        items = [model_class.model_validate(item) for item in data.get(list_key, [])]
        # Browse uses <list_key_singular>-count and <list_key_singular>-offset
        singular = entity_type
        return BrowseResult(
            items=items,
            count=data.get(f"{singular}-count", 0),
            offset=data.get(f"{singular}-offset", 0),
        )
