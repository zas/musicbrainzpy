"""Test fixtures and shared mock data."""

from __future__ import annotations

from collections.abc import Generator

import pytest
import respx

from musicbrainzpy.client import MusicBrainzClient

ARTIST_LOOKUP_RESPONSE = {
    "id": "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab",
    "name": "Metallica",
    "sort-name": "Metallica",
    "type": "Group",
    "country": "US",
    "life-span": {"begin": "1981-10", "ended": False},
}

ARTIST_SEARCH_RESPONSE = {
    "created": "2024-01-01T00:00:00.000Z",
    "count": 1,
    "offset": 0,
    "artists": [
        {
            "id": "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab",
            "name": "Metallica",
            "sort-name": "Metallica",
            "score": 100,
        }
    ],
}

RELEASE_BROWSE_RESPONSE = {
    "release-offset": 0,
    "release-count": 1,
    "releases": [
        {
            "id": "b84ee12a-09ef-421b-82de-0441a926375b",
            "title": "Master of Puppets",
            "status": "Official",
            "date": "1986-03-03",
        }
    ],
}


@pytest.fixture
def client() -> MusicBrainzClient:
    """Create a client with rate limiting disabled for tests."""
    return MusicBrainzClient("test-app", "0.1.0", "test@example.com", rate_limit=0)


@pytest.fixture
def mock_api() -> Generator[respx.MockRouter]:
    """Activate respx mocking for the MusicBrainz API."""
    with respx.mock(base_url="https://musicbrainz.org/ws/2") as router:
        yield router
