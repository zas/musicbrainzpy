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

ISRC_LOOKUP_RESPONSE = {
    "recordings": [
        {
            "id": "ba5d0553-032f-4127-aed7-4d2e0d18f3f9",
            "title": "Enter Sandman",
            "disambiguation": "",
            "length": 331160,
        }
    ],
}

ISWC_LOOKUP_RESPONSE = {
    "works": [
        {
            "id": "be5e4e89-20a0-3687-8a0e-5e3a2a3b1e42",
            "title": "Enter Sandman",
            "type": "Song",
            "language": "eng",
            "languages": ["eng"],
            "iswcs": ["T-070.116.274-5"],
        }
    ],
}

DISCID_LOOKUP_RESPONSE = {
    "releases": [
        {
            "id": "d87a6b90-7a9e-4ca1-a170-194bf443e2e9",
            "title": "Metallica",
            "status": "Official",
            "date": "1991-08-12",
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
