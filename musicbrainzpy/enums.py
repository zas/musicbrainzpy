"""Enums for MusicBrainz entity types, release statuses, and release group types."""

from __future__ import annotations

from enum import Enum


class _StrEnum(str, Enum):
    """str-valued enum compatible with Python 3.10+."""


class EntityType(_StrEnum):
    """Core MusicBrainz entity types."""

    AREA = "area"
    ARTIST = "artist"
    EVENT = "event"
    GENRE = "genre"
    INSTRUMENT = "instrument"
    LABEL = "label"
    PLACE = "place"
    RECORDING = "recording"
    RELEASE = "release"
    RELEASE_GROUP = "release-group"
    SERIES = "series"
    WORK = "work"
    URL = "url"


class ReleaseStatus(_StrEnum):
    OFFICIAL = "official"
    PROMOTION = "promotion"
    BOOTLEG = "bootleg"
    PSEUDO_RELEASE = "pseudo-release"
    WITHDRAWN = "withdrawn"
    CANCELLED = "cancelled"


class ReleaseGroupType(_StrEnum):
    ALBUM = "album"
    SINGLE = "single"
    EP = "ep"
    BROADCAST = "broadcast"
    OTHER = "other"


class ReleaseGroupSecondaryType(_StrEnum):
    AUDIO_DRAMA = "audio drama"
    AUDIOBOOK = "audiobook"
    COMPILATION = "compilation"
    DEMO = "demo"
    DJ_MIX = "dj-mix"
    FIELD_RECORDING = "field recording"
    INTERVIEW = "interview"
    LIVE = "live"
    MIXTAPE_STREET = "mixtape/street"
    REMIX = "remix"
    SOUNDTRACK = "soundtrack"
    SPOKENWORD = "spokenword"


class OAuthScope(_StrEnum):
    """OAuth2 scopes for MusicBrainz API authorization."""

    PROFILE = "profile"
    EMAIL = "email"
    TAG = "tag"
    RATING = "rating"
    COLLECTION = "collection"
    SUBMIT_ISRC = "submit_isrc"
    SUBMIT_BARCODE = "submit_barcode"
