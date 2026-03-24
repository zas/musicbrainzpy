"""Tests for the Cover Art Archive client."""

from __future__ import annotations

import httpx
import pytest
import respx

from musicbrainzpy.coverart import CoverArtClient, SyncCoverArtClient
from musicbrainzpy.exceptions import NotFoundError
from musicbrainzpy.models.coverart import CoverArtImageList

RELEASE_MBID = "76df3287-6cda-33eb-8e9a-044b5e15ffdd"
RG_MBID = "c31a5e2b-0bf8-32e0-8aeb-ef4ba9973932"

IMAGE_LIST_RESPONSE = {
    "images": [
        {
            "types": ["Front"],
            "front": True,
            "back": False,
            "edit": 17462565,
            "image": f"http://coverartarchive.org/release/{RELEASE_MBID}/829521842.jpg",
            "comment": "",
            "approved": True,
            "id": 829521842,
            "thumbnails": {
                "250": f"http://coverartarchive.org/release/{RELEASE_MBID}/829521842-250.jpg",
                "500": f"http://coverartarchive.org/release/{RELEASE_MBID}/829521842-500.jpg",
                "1200": f"http://coverartarchive.org/release/{RELEASE_MBID}/829521842-1200.jpg",
                "small": f"http://coverartarchive.org/release/{RELEASE_MBID}/829521842-250.jpg",
                "large": f"http://coverartarchive.org/release/{RELEASE_MBID}/829521842-500.jpg",
            },
        }
    ],
    "release": f"http://musicbrainz.org/release/{RELEASE_MBID}",
}

DUMMY_IMAGE = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def caa_client() -> CoverArtClient:
    return CoverArtClient("test-app", "0.1.0", "test@example.com")


@pytest.fixture
def mock_caa() -> respx.MockRouter:
    """Context-managed respx mock for the CAA."""
    # We use a non-context-manager approach so pytest can manage it
    return respx.MockRouter(base_url="https://coverartarchive.org")


class TestCoverArtModels:
    def test_deserialize_image_list(self) -> None:
        result = CoverArtImageList.model_validate(IMAGE_LIST_RESPONSE)
        assert len(result.images) == 1
        img = result.images[0]
        assert img.front is True
        assert img.back is False
        assert img.types == ["Front"]
        assert img.id == 829521842
        assert img.thumbnails.t250 is not None
        assert img.thumbnails.t500 is not None
        assert img.thumbnails.t1200 is not None
        assert img.thumbnails.small is not None


class TestCoverArtClient:
    async def test_get_image_list(self, caa_client: CoverArtClient) -> None:
        with respx.mock(base_url="https://coverartarchive.org") as mock:
            mock.get(f"/release/{RELEASE_MBID}/").mock(return_value=httpx.Response(200, json=IMAGE_LIST_RESPONSE))
            result = await caa_client.get_image_list(RELEASE_MBID)
            assert isinstance(result, CoverArtImageList)
            assert len(result.images) == 1
            assert result.images[0].front is True

    async def test_get_release_group_image_list(self, caa_client: CoverArtClient) -> None:
        with respx.mock(base_url="https://coverartarchive.org") as mock:
            mock.get(f"/release-group/{RG_MBID}/").mock(return_value=httpx.Response(200, json=IMAGE_LIST_RESPONSE))
            result = await caa_client.get_release_group_image_list(RG_MBID)
            assert isinstance(result, CoverArtImageList)

    async def test_get_front(self, caa_client: CoverArtClient) -> None:
        with respx.mock(base_url="https://coverartarchive.org") as mock:
            mock.get(f"/release/{RELEASE_MBID}/front").mock(return_value=httpx.Response(200, content=DUMMY_IMAGE))
            data = await caa_client.get_front(RELEASE_MBID)
            assert data == DUMMY_IMAGE

    async def test_get_front_with_size(self, caa_client: CoverArtClient) -> None:
        with respx.mock(base_url="https://coverartarchive.org") as mock:
            mock.get(f"/release/{RELEASE_MBID}/front-500").mock(return_value=httpx.Response(200, content=DUMMY_IMAGE))
            data = await caa_client.get_front(RELEASE_MBID, size=500)
            assert data == DUMMY_IMAGE

    async def test_get_back(self, caa_client: CoverArtClient) -> None:
        with respx.mock(base_url="https://coverartarchive.org") as mock:
            mock.get(f"/release/{RELEASE_MBID}/back").mock(return_value=httpx.Response(200, content=DUMMY_IMAGE))
            data = await caa_client.get_back(RELEASE_MBID)
            assert data == DUMMY_IMAGE

    async def test_get_image_by_id(self, caa_client: CoverArtClient) -> None:
        with respx.mock(base_url="https://coverartarchive.org") as mock:
            mock.get(f"/release/{RELEASE_MBID}/829521842").mock(return_value=httpx.Response(200, content=DUMMY_IMAGE))
            data = await caa_client.get_image(RELEASE_MBID, "829521842")
            assert data == DUMMY_IMAGE

    async def test_get_image_by_id_with_size(self, caa_client: CoverArtClient) -> None:
        with respx.mock(base_url="https://coverartarchive.org") as mock:
            mock.get(f"/release/{RELEASE_MBID}/829521842-250").mock(
                return_value=httpx.Response(200, content=DUMMY_IMAGE)
            )
            data = await caa_client.get_image(RELEASE_MBID, "829521842", size=250)
            assert data == DUMMY_IMAGE

    async def test_get_release_group_front(self, caa_client: CoverArtClient) -> None:
        with respx.mock(base_url="https://coverartarchive.org") as mock:
            mock.get(f"/release-group/{RG_MBID}/front").mock(return_value=httpx.Response(200, content=DUMMY_IMAGE))
            data = await caa_client.get_release_group_front(RG_MBID)
            assert data == DUMMY_IMAGE

    async def test_not_found(self, caa_client: CoverArtClient) -> None:
        with respx.mock(base_url="https://coverartarchive.org") as mock:
            mock.get(f"/release/{RELEASE_MBID}/").mock(return_value=httpx.Response(404, text="Not Found"))
            with pytest.raises(NotFoundError):
                await caa_client.get_image_list(RELEASE_MBID)


class TestSyncCoverArtClient:
    def test_get_image_list(self) -> None:
        with respx.mock(base_url="https://coverartarchive.org") as mock:
            mock.get(f"/release/{RELEASE_MBID}/").mock(return_value=httpx.Response(200, json=IMAGE_LIST_RESPONSE))
            with SyncCoverArtClient("test", "0.1", "test@example.com") as c:
                result = c.get_image_list(RELEASE_MBID)
                assert isinstance(result, CoverArtImageList)
                assert len(result.images) == 1

    def test_get_front(self) -> None:
        with respx.mock(base_url="https://coverartarchive.org") as mock:
            mock.get(f"/release/{RELEASE_MBID}/front").mock(return_value=httpx.Response(200, content=DUMMY_IMAGE))
            with SyncCoverArtClient("test", "0.1", "test@example.com") as c:
                data = c.get_front(RELEASE_MBID)
                assert data == DUMMY_IMAGE
