"""Cover Art Archive client.

Async and sync clients for the Cover Art Archive (coverartarchive.org).
Separate from the main MusicBrainz API — different host, no auth required.
"""

from __future__ import annotations

from typing import Literal

import httpx

from musicbrainzpy.client import _build_user_agent, _raise_for_status
from musicbrainzpy.models.coverart import CoverArtImageList

DEFAULT_CAA_BASE_URL = "https://coverartarchive.org/"

ImageSize = Literal[250, 500, 1200]


def _image_path(entity_type: str, mbid: str, image_id: str, size: ImageSize | None = None) -> str:
    """Build the URL path for an image request."""
    suffix = f"-{size}" if size else ""
    return f"{entity_type}/{mbid}/{image_id}{suffix}"


class CoverArtClient:
    """Async client for the Cover Art Archive.

    Args:
        app_name: Application name for User-Agent.
        app_version: Application version for User-Agent.
        app_contact: Contact URL or email for User-Agent.
        base_url: CAA base URL. Defaults to the official endpoint.
    """

    def __init__(
        self,
        app_name: str,
        app_version: str,
        app_contact: str,
        *,
        base_url: str = DEFAULT_CAA_BASE_URL,
    ) -> None:
        self._base_url = base_url.rstrip("/") + "/"
        self._client = httpx.AsyncClient(
            headers={"User-Agent": _build_user_agent(app_name, app_version, app_contact)},
            follow_redirects=True,
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> CoverArtClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def _get_json(self, path: str) -> dict:
        """GET a JSON response."""
        response = await self._client.get(self._base_url + path, headers={"Accept": "application/json"})
        _raise_for_status(response)
        return response.json()

    async def _get_bytes(self, path: str) -> bytes:
        """GET binary image data."""
        response = await self._client.get(self._base_url + path)
        _raise_for_status(response)
        return response.content

    # --- JSON listings ---

    async def get_image_list(self, release_id: str) -> CoverArtImageList:
        """Get the list of cover art for a release.

        Args:
            release_id: MusicBrainz release MBID.
        """
        data = await self._get_json(f"release/{release_id}/")
        return CoverArtImageList.model_validate(data)

    async def get_release_group_image_list(self, release_group_id: str) -> CoverArtImageList:
        """Get the list of cover art for a release group.

        Args:
            release_group_id: MusicBrainz release group MBID.
        """
        data = await self._get_json(f"release-group/{release_group_id}/")
        return CoverArtImageList.model_validate(data)

    # --- Binary image downloads ---

    async def get_image(
        self, mbid: str, cover_id: str, *, size: ImageSize | None = None, entity_type: str = "release"
    ) -> bytes:
        """Download a specific cover art image.

        Args:
            mbid: MusicBrainz release or release group MBID.
            cover_id: Image ID from the listing, or ``"front"``/``"back"``.
            size: Thumbnail size (250, 500, 1200) or None for full-size.
            entity_type: ``"release"`` or ``"release-group"``.
        """
        return await self._get_bytes(_image_path(entity_type, mbid, cover_id, size))

    async def get_front(self, release_id: str, *, size: ImageSize | None = None) -> bytes:
        """Download the front cover art for a release.

        Args:
            release_id: MusicBrainz release MBID.
            size: Thumbnail size (250, 500, 1200) or None for full-size.
        """
        return await self.get_image(release_id, "front", size=size)

    async def get_back(self, release_id: str, *, size: ImageSize | None = None) -> bytes:
        """Download the back cover art for a release.

        Args:
            release_id: MusicBrainz release MBID.
            size: Thumbnail size (250, 500, 1200) or None for full-size.
        """
        return await self.get_image(release_id, "back", size=size)

    async def get_release_group_front(self, release_group_id: str, *, size: ImageSize | None = None) -> bytes:
        """Download the front cover art for a release group.

        Args:
            release_group_id: MusicBrainz release group MBID.
            size: Thumbnail size (250, 500, 1200) or None for full-size.
        """
        return await self.get_image(release_group_id, "front", size=size, entity_type="release-group")


class SyncCoverArtClient:
    """Synchronous client for the Cover Art Archive.

    Args:
        app_name: Application name for User-Agent.
        app_version: Application version for User-Agent.
        app_contact: Contact URL or email for User-Agent.
        base_url: CAA base URL. Defaults to the official endpoint.
    """

    def __init__(
        self,
        app_name: str,
        app_version: str,
        app_contact: str,
        *,
        base_url: str = DEFAULT_CAA_BASE_URL,
    ) -> None:
        self._base_url = base_url.rstrip("/") + "/"
        self._client = httpx.Client(
            headers={"User-Agent": _build_user_agent(app_name, app_version, app_contact)},
            follow_redirects=True,
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> SyncCoverArtClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _get_json(self, path: str) -> dict:
        """GET a JSON response."""
        response = self._client.get(self._base_url + path, headers={"Accept": "application/json"})
        _raise_for_status(response)
        return response.json()

    def _get_bytes(self, path: str) -> bytes:
        """GET binary image data."""
        response = self._client.get(self._base_url + path)
        _raise_for_status(response)
        return response.content

    def get_image_list(self, release_id: str) -> CoverArtImageList:
        """Get the list of cover art for a release. See :meth:`CoverArtClient.get_image_list`."""
        data = self._get_json(f"release/{release_id}/")
        return CoverArtImageList.model_validate(data)

    def get_release_group_image_list(self, release_group_id: str) -> CoverArtImageList:
        """Get the list of cover art for a release group. See :meth:`CoverArtClient.get_release_group_image_list`."""
        data = self._get_json(f"release-group/{release_group_id}/")
        return CoverArtImageList.model_validate(data)

    def get_image(
        self, mbid: str, cover_id: str, *, size: ImageSize | None = None, entity_type: str = "release"
    ) -> bytes:
        """Download a specific cover art image. See :meth:`CoverArtClient.get_image`."""
        return self._get_bytes(_image_path(entity_type, mbid, cover_id, size))

    def get_front(self, release_id: str, *, size: ImageSize | None = None) -> bytes:
        """Download the front cover art for a release. See :meth:`CoverArtClient.get_front`."""
        return self.get_image(release_id, "front", size=size)

    def get_back(self, release_id: str, *, size: ImageSize | None = None) -> bytes:
        """Download the back cover art for a release. See :meth:`CoverArtClient.get_back`."""
        return self.get_image(release_id, "back", size=size)

    def get_release_group_front(self, release_group_id: str, *, size: ImageSize | None = None) -> bytes:
        """Download the front cover art for a release group. See :meth:`CoverArtClient.get_release_group_front`."""
        return self.get_image(release_group_id, "front", size=size, entity_type="release-group")
