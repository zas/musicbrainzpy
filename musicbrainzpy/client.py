"""MusicBrainz API client.

Async-first HTTP client for the MusicBrainz JSON API.
Handles rate limiting, User-Agent, and error mapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from musicbrainzpy._ratelimit import RateLimiter
from musicbrainzpy._xml import build_barcode_xml, build_isrc_xml, build_rating_xml, build_tag_xml
from musicbrainzpy.auth import OAuthHandler, make_digest_auth
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

    Supports two authentication methods (for submissions and user data):

    - **Digest auth**: pass ``username`` and ``password``.
    - **OAuth2**: pass an :class:`~musicbrainzpy.auth.OAuthHandler` instance.

    Args:
        app_name: Application name for User-Agent.
        app_version: Application version for User-Agent.
        app_contact: Contact URL or email for User-Agent.
        base_url: API base URL. Defaults to the official endpoint.
        rate_limit: Minimum seconds between requests. Set to 0 to disable.
        username: MusicBrainz username for digest auth.
        password: MusicBrainz password for digest auth.
        oauth: An :class:`~musicbrainzpy.auth.OAuthHandler` for OAuth2 auth.
    """

    def __init__(
        self,
        app_name: str,
        app_version: str,
        app_contact: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        rate_limit: float = 1.0,
        username: str | None = None,
        password: str | None = None,
        oauth: OAuthHandler | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/") + "/"
        self._rate_limiter = RateLimiter(interval=rate_limit)
        self._digest_auth = make_digest_auth(username, password) if username and password else None
        self._oauth = oauth
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

    async def _get_auth_kwargs(self) -> dict[str, Any]:
        """Build auth kwargs for an authenticated request.

        Returns dict with either ``auth=`` (digest) or ``headers=`` (OAuth2 bearer).

        Raises:
            AuthenticationError: If no credentials were configured.
        """
        if self._oauth:
            token = await self._oauth.get_access_token()
            return {"headers": {"Authorization": f"Bearer {token}"}}
        if self._digest_auth:
            return {"auth": self._digest_auth}
        raise AuthenticationError("Authentication required. Provide username/password or an OAuthHandler.")

    @property
    def is_authenticated(self) -> bool:
        """Whether any authentication method is configured."""
        return self._digest_auth is not None or self._oauth is not None

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

    async def _get_authenticated(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Perform a rate-limited authenticated GET (for user-tags, user-ratings, etc.)."""
        auth_kwargs = await self._get_auth_kwargs()
        await self._rate_limiter.acquire()
        url = self._base_url + path
        all_params = {"fmt": "json"}
        if params:
            all_params.update(params)
        response = await self._client.get(url, params=all_params, **auth_kwargs)
        _raise_for_status(response)
        return response.json()

    async def _post(self, path: str, *, params: dict[str, str], body: str) -> None:
        """Perform a rate-limited authenticated POST with XML body.

        Args:
            path: API path (e.g. ``"tag"``).
            params: Query parameters (must include ``client``).
            body: XML request body.

        Raises:
            AuthenticationError: If no credentials were provided.
        """
        auth_kwargs = await self._get_auth_kwargs()
        await self._rate_limiter.acquire()
        url = self._base_url + path
        all_params = {"fmt": "json", **params}
        headers: dict[str, str] = {"Content-Type": "application/xml; charset=utf-8"}
        # Merge bearer token header if using OAuth2
        if "headers" in auth_kwargs:
            headers.update(auth_kwargs["headers"])
        response = await self._client.post(
            url,
            params=all_params,
            content=body,
            headers=headers,
            auth=auth_kwargs.get("auth"),  # type: ignore[arg-type]
        )
        _raise_for_status(response)

    async def _put(self, path: str, *, params: dict[str, str]) -> None:
        """Perform a rate-limited authenticated PUT (for collections).

        Args:
            path: Full API path including entity IDs.
            params: Query parameters (must include ``client``).

        Raises:
            AuthenticationError: If no credentials were provided.
        """
        auth_kwargs = await self._get_auth_kwargs()
        await self._rate_limiter.acquire()
        url = self._base_url + path
        response = await self._client.put(url, params=params, **auth_kwargs)
        _raise_for_status(response)

    async def _delete(self, path: str, *, params: dict[str, str]) -> None:
        """Perform a rate-limited authenticated DELETE (for collections).

        Args:
            path: Full API path including entity IDs.
            params: Query parameters (must include ``client``).

        Raises:
            AuthenticationError: If no credentials were provided.
        """
        auth_kwargs = await self._get_auth_kwargs()
        await self._rate_limiter.acquire()
        url = self._base_url + path
        response = await self._client.delete(url, params=params, **auth_kwargs)
        _raise_for_status(response)

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

    # --- Non-MBID lookups ---

    async def lookup_by_isrc(self, isrc: str, includes: list[str] | None = None) -> list[Recording]:
        """Look up recordings by ISRC.

        Args:
            isrc: International Standard Recording Code.
            includes: Optional ``inc=`` subqueries for recordings.
        """
        params: dict[str, str] = {}
        if includes:
            params["inc"] = "+".join(includes)
        data = await self._get(f"isrc/{isrc}", params)
        return [Recording.model_validate(r) for r in data.get("recordings", [])]

    async def lookup_by_iswc(self, iswc: str, includes: list[str] | None = None) -> list[Work]:
        """Look up works by ISWC.

        Args:
            iswc: International Standard Musical Work Code.
            includes: Optional ``inc=`` subqueries for works.
        """
        params: dict[str, str] = {}
        if includes:
            params["inc"] = "+".join(includes)
        data = await self._get(f"iswc/{iswc}", params)
        return [Work.model_validate(w) for w in data.get("work-list", {}).get("work", [])]

    async def lookup_by_discid(
        self,
        discid: str,
        *,
        toc: str | None = None,
        cdstubs: bool = True,
        media_format: str | None = None,
        includes: list[str] | None = None,
    ) -> list[Release]:
        """Look up releases by disc ID.

        Args:
            discid: The disc ID (or ``"-"`` for TOC-only lookup).
            toc: Table of contents for fuzzy matching.
            cdstubs: Whether to include CD stubs (default True).
            media_format: Filter by media format (e.g. ``"all"``).
            includes: Optional ``inc=`` subqueries for releases.
        """
        params: dict[str, str] = {}
        if toc:
            params["toc"] = toc
        if not cdstubs:
            params["cdstubs"] = "no"
        if media_format:
            params["media-format"] = media_format
        if includes:
            params["inc"] = "+".join(includes)
        data = await self._get(f"discid/{discid}", params)
        return [Release.model_validate(r) for r in data.get("releases", [])]

    async def lookup_by_url(self, *urls: str) -> dict[str, Any]:
        """Look up URL entities by resource URL.

        Args:
            urls: One or more URLs to look up (max 100).
        """
        params: dict[str, str | list[str]] = {"resource": list(urls)} if len(urls) > 1 else {"resource": urls[0]}
        return await self._get("url", params)  # type: ignore[arg-type]

    # --- Submissions (require auth) ---

    async def submit_tags(self, client_id: str, entities: dict[str, dict[str, list[str]]]) -> None:
        """Submit tags/genres for entities.

        Args:
            client_id: Application identifier (e.g. ``"myapp-1.0"``).
            entities: Mapping of entity type → {mbid: [tag_names]}.
        """
        body = build_tag_xml(entities)
        await self._post("tag", params={"client": client_id}, body=body)

    async def submit_ratings(self, client_id: str, entities: dict[str, dict[str, int]]) -> None:
        """Submit ratings for entities.

        Args:
            client_id: Application identifier.
            entities: Mapping of entity type → {mbid: rating (0-100)}.
        """
        body = build_rating_xml(entities)
        await self._post("rating", params={"client": client_id}, body=body)

    async def submit_barcodes(self, client_id: str, barcodes: dict[str, str]) -> None:
        """Submit barcodes for releases.

        Args:
            client_id: Application identifier.
            barcodes: Mapping of release MBID → barcode (EAN/UPC).
        """
        body = build_barcode_xml(barcodes)
        await self._post("release/", params={"client": client_id}, body=body)

    async def submit_isrcs(self, client_id: str, isrcs: dict[str, list[str]]) -> None:
        """Submit ISRCs for recordings.

        Args:
            client_id: Application identifier.
            isrcs: Mapping of recording MBID → list of ISRCs.
        """
        body = build_isrc_xml(isrcs)
        await self._post("recording/", params={"client": client_id}, body=body)

    async def collection_add(self, client_id: str, collection_id: str, entity_type: str, mbids: list[str]) -> None:
        """Add entities to a collection.

        Args:
            client_id: Application identifier.
            collection_id: MBID of the collection.
            entity_type: Entity type plural (e.g. ``"releases"``, ``"artists"``).
            mbids: List of entity MBIDs to add (max ~400).
        """
        ids = ";".join(mbids)
        await self._put(f"collection/{collection_id}/{entity_type}/{ids}", params={"client": client_id})

    async def collection_remove(self, client_id: str, collection_id: str, entity_type: str, mbids: list[str]) -> None:
        """Remove entities from a collection.

        Args:
            client_id: Application identifier.
            collection_id: MBID of the collection.
            entity_type: Entity type plural (e.g. ``"releases"``, ``"artists"``).
            mbids: List of entity MBIDs to remove.
        """
        ids = ";".join(mbids)
        await self._delete(f"collection/{collection_id}/{entity_type}/{ids}", params={"client": client_id})
