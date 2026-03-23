"""Pydantic models for MusicBrainz entities."""

from __future__ import annotations

from musicbrainzpy.models.area import Area
from musicbrainzpy.models.artist import Artist
from musicbrainzpy.models.common import (
    Alias,
    AreaStub,
    ArtistCredit,
    ArtistStub,
    Genre,
    LifeSpan,
    MBModel,
    Rating,
    ReleaseEvent,
    Tag,
    TextRepresentation,
)
from musicbrainzpy.models.event import Event
from musicbrainzpy.models.genre import GenreFull
from musicbrainzpy.models.instrument import Instrument
from musicbrainzpy.models.label import Label
from musicbrainzpy.models.place import Coordinates, Place
from musicbrainzpy.models.recording import Recording
from musicbrainzpy.models.release import LabelInfo, LabelStub, Medium, Release, Track
from musicbrainzpy.models.release_group import ReleaseGroup
from musicbrainzpy.models.series import Series
from musicbrainzpy.models.url import Url
from musicbrainzpy.models.work import Work

__all__ = [
    "Alias",
    "Area",
    "AreaStub",
    "Artist",
    "ArtistCredit",
    "ArtistStub",
    "Coordinates",
    "Event",
    "Genre",
    "GenreFull",
    "Instrument",
    "Label",
    "LabelInfo",
    "LabelStub",
    "LifeSpan",
    "MBModel",
    "Medium",
    "Place",
    "Rating",
    "Recording",
    "Release",
    "ReleaseEvent",
    "ReleaseGroup",
    "Series",
    "Tag",
    "TextRepresentation",
    "Track",
    "Url",
    "Work",
]
