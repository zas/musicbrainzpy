"""Tests for Pydantic model deserialization."""

from __future__ import annotations

from musicbrainzpy.models import (
    Area,
    Artist,
    Event,
    GenreFull,
    Instrument,
    Label,
    Place,
    Recording,
    Release,
    ReleaseGroup,
    Series,
    Url,
    Work,
)

# --- Sample JSON payloads (derived from real API responses) ---

ARTIST_JSON = {
    "id": "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab",
    "name": "Metallica",
    "sort-name": "Metallica",
    "type": "Group",
    "type-id": "e431f5f6-b5d2-343d-8b36-72607fffb74b",
    "country": "US",
    "disambiguation": "",
    "life-span": {"begin": "1981-10-28", "ended": False, "end": None},
    "area": {
        "id": "489ce91b-6658-3307-9877-795b68554c98",
        "name": "United States",
        "sort-name": "United States",
        "iso-3166-1-codes": ["US"],
    },
    "begin-area": {
        "id": "1f40c6e1-47ba-4e35-996f-fe6ee5840e62",
        "name": "Los Angeles",
        "sort-name": "Los Angeles",
    },
    "isnis": ["0000000122939631"],
    "aliases": [
        {
            "name": "Metalica",
            "sort-name": "Metalica",
            "type": "Search hint",
            "type-id": "1937e404-b981-3cb7-8151-4c86ebfc8d8e",
            "locale": None,
            "primary": None,
            "begin": None,
            "end": None,
            "ended": False,
        }
    ],
    "tags": [{"name": "thrash metal", "count": 65}],
    "genres": [{"id": "cc4cf136-5690-4ee3-a62b-b172febfe322", "name": "thrash metal", "count": 65}],
    "rating": {"value": 4.15, "votes-count": 73},
}

RECORDING_JSON = {
    "id": "ba5d0553-032f-4127-aed7-4d2e0d18f3f9",
    "title": "Enter Sandman",
    "disambiguation": "",
    "length": 331160,
    "video": False,
    "first-release-date": "1991-08-12",
    "artist-credit": [
        {
            "name": "Metallica",
            "joinphrase": "",
            "artist": {
                "id": "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab",
                "name": "Metallica",
                "sort-name": "Metallica",
            },
        }
    ],
    "isrcs": ["USEE10100063"],
}

RELEASE_JSON = {
    "id": "d87a6b90-7a9e-4ca1-a170-194bf443e2e9",
    "title": "Metallica",
    "status": "Official",
    "status-id": "4e304316-386d-3409-af2e-78857eec5cfe",
    "date": "1991-08-12",
    "country": "AU",
    "barcode": "731451002229",
    "packaging": "Jewel Case",
    "text-representation": {"language": "eng", "script": "Latn"},
    "artist-credit": [
        {
            "name": "Metallica",
            "joinphrase": "",
            "artist": {"id": "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab", "name": "Metallica", "sort-name": "Metallica"},
        }
    ],
    "media": [{"position": 1, "format": "CD", "format-id": "9712d52a-4509-3d4b-a1a2-67c88c643e31", "track-count": 12}],
    "label-info": [{"catalog-number": "510 022-2", "label": {"id": "some-id", "name": "Vertigo"}}],
}

RELEASE_GROUP_JSON = {
    "id": "e8f70201-8899-3f0c-9e07-5d6495bc8046",
    "title": "Metallica",
    "primary-type": "Album",
    "secondary-types": [],
    "first-release-date": "1991-08-12",
    "disambiguation": "\u201cThe Black Album\u201d",
    "genres": [{"id": "a6719055-99c4-47eb-beaa-71081f2376f9", "name": "heavy metal", "count": 28}],
}

LABEL_JSON = {
    "id": "c029628b-6633-439e-bcee-ed02e8a338f7",
    "name": "EMI",
    "sort-name": "EMI",
    "type": "Original Production",
    "label-code": 542,
    "country": "GB",
    "life-span": {"begin": "1931", "end": "2012", "ended": True},
}

WORK_JSON = {
    "id": "be5e4e89-20a0-3687-8a0e-5e3a2a3b1e42",
    "title": "Enter Sandman",
    "type": "Song",
    "language": "eng",
    "languages": ["eng"],
    "iswcs": ["T-070.116.274-5"],
}

AREA_JSON = {
    "id": "489ce91b-6658-3307-9877-795b68554c98",
    "name": "United States",
    "sort-name": "United States",
    "type": "Country",
    "iso-3166-1-codes": ["US"],
}

EVENT_JSON = {
    "id": "some-event-id",
    "name": "Metallica at Wembley",
    "type": "Concert",
    "cancelled": False,
    "life-span": {"begin": "2019-06-20", "end": "2019-06-20", "ended": True},
}

PLACE_JSON = {
    "id": "some-place-id",
    "name": "Wembley Stadium",
    "type": "Venue",
    "address": "London, UK",
    "coordinates": {"latitude": 51.556, "longitude": -0.2795},
    "area": {"id": "some-area-id", "name": "London", "sort-name": "London"},
}

INSTRUMENT_JSON = {
    "id": "some-instrument-id",
    "name": "guitar",
    "type": "String instrument",
    "description": "A fretted string instrument.",
}

SERIES_JSON = {
    "id": "some-series-id",
    "name": "Metallica World Tour",
    "type": "Tour",
}

GENRE_JSON = {
    "id": "cc4cf136-5690-4ee3-a62b-b172febfe322",
    "name": "thrash metal",
    "disambiguation": "",
}

URL_JSON = {
    "id": "some-url-id",
    "resource": "https://www.metallica.com/",
}


# --- Tests ---


class TestArtist:
    def test_deserialize(self) -> None:
        a = Artist.model_validate(ARTIST_JSON)
        assert a.id == "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"
        assert a.name == "Metallica"
        assert a.sort_name == "Metallica"
        assert a.type == "Group"
        assert a.country == "US"
        assert a.life_span is not None
        assert a.life_span.begin == "1981-10-28"
        assert a.life_span.ended is False
        assert a.area is not None
        assert a.area.name == "United States"
        assert a.area.iso_3166_1_codes == ["US"]
        assert a.begin_area is not None
        assert a.begin_area.name == "Los Angeles"
        assert a.isnis == ["0000000122939631"]

    def test_optional_includes(self) -> None:
        a = Artist.model_validate(ARTIST_JSON)
        assert a.aliases is not None
        assert len(a.aliases) == 1
        assert a.aliases[0].name == "Metalica"
        assert a.tags is not None
        assert a.tags[0].name == "thrash metal"
        assert a.genres is not None
        assert a.genres[0].count == 65
        assert a.rating is not None
        assert a.rating.value == 4.15
        assert a.rating.votes_count == 73

    def test_missing_includes(self) -> None:
        minimal = {"id": "abc", "name": "Test", "sort-name": "Test"}
        a = Artist.model_validate(minimal)
        assert a.aliases is None
        assert a.tags is None
        assert a.genres is None
        assert a.rating is None

    def test_extra_fields_preserved(self) -> None:
        data = {**ARTIST_JSON, "new-future-field": "value"}
        a = Artist.model_validate(data)
        assert a.model_extra is not None
        assert a.model_extra["new-future-field"] == "value"


class TestRecording:
    def test_deserialize(self) -> None:
        r = Recording.model_validate(RECORDING_JSON)
        assert r.title == "Enter Sandman"
        assert r.length == 331160
        assert r.video is False
        assert r.first_release_date == "1991-08-12"
        assert r.artist_credit is not None
        assert r.artist_credit[0].artist.name == "Metallica"
        assert r.isrcs == ["USEE10100063"]


class TestRelease:
    def test_deserialize(self) -> None:
        r = Release.model_validate(RELEASE_JSON)
        assert r.title == "Metallica"
        assert r.status == "Official"
        assert r.barcode == "731451002229"
        assert r.text_representation is not None
        assert r.text_representation.language == "eng"
        assert r.media is not None
        assert r.media[0].track_count == 12
        assert r.media[0].format == "CD"
        assert r.label_info is not None
        assert r.label_info[0].catalog_number == "510 022-2"
        assert r.label_info[0].label is not None
        assert r.label_info[0].label.name == "Vertigo"


class TestReleaseGroup:
    def test_deserialize(self) -> None:
        rg = ReleaseGroup.model_validate(RELEASE_GROUP_JSON)
        assert rg.title == "Metallica"
        assert rg.primary_type == "Album"
        assert rg.secondary_types == []
        assert rg.first_release_date == "1991-08-12"
        assert rg.genres is not None
        assert rg.genres[0].name == "heavy metal"


class TestLabel:
    def test_deserialize(self) -> None:
        lb = Label.model_validate(LABEL_JSON)
        assert lb.name == "EMI"
        assert lb.type == "Original Production"
        assert lb.label_code == 542
        assert lb.life_span is not None
        assert lb.life_span.ended is True


class TestWork:
    def test_deserialize(self) -> None:
        w = Work.model_validate(WORK_JSON)
        assert w.title == "Enter Sandman"
        assert w.type == "Song"
        assert w.iswcs == ["T-070.116.274-5"]
        assert w.languages == ["eng"]


class TestArea:
    def test_deserialize(self) -> None:
        a = Area.model_validate(AREA_JSON)
        assert a.name == "United States"
        assert a.iso_3166_1_codes == ["US"]


class TestEvent:
    def test_deserialize(self) -> None:
        e = Event.model_validate(EVENT_JSON)
        assert e.name == "Metallica at Wembley"
        assert e.cancelled is False
        assert e.life_span is not None
        assert e.life_span.begin == "2019-06-20"


class TestPlace:
    def test_deserialize(self) -> None:
        p = Place.model_validate(PLACE_JSON)
        assert p.name == "Wembley Stadium"
        assert p.coordinates is not None
        assert p.coordinates.latitude == 51.556
        assert p.area is not None
        assert p.area.name == "London"


class TestInstrument:
    def test_deserialize(self) -> None:
        i = Instrument.model_validate(INSTRUMENT_JSON)
        assert i.name == "guitar"
        assert i.description == "A fretted string instrument."


class TestSeries:
    def test_deserialize(self) -> None:
        s = Series.model_validate(SERIES_JSON)
        assert s.name == "Metallica World Tour"
        assert s.type == "Tour"


class TestGenreFull:
    def test_deserialize(self) -> None:
        g = GenreFull.model_validate(GENRE_JSON)
        assert g.name == "thrash metal"


class TestUrl:
    def test_deserialize(self) -> None:
        u = Url.model_validate(URL_JSON)
        assert u.resource == "https://www.metallica.com/"
