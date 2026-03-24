"""Pydantic models for MusicBrainz entities."""

from __future__ import annotations

from musicbrainzpy.models.annotation import Annotation
from musicbrainzpy.models.area import Area
from musicbrainzpy.models.artist import Artist
from musicbrainzpy.models.collection import Collection
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
from musicbrainzpy.models.release import CoverArtArchive, LabelInfo, LabelStub, Medium, Release, ReleaseGroupStub, Track
from musicbrainzpy.models.release_group import ReleaseGroup
from musicbrainzpy.models.series import Series
from musicbrainzpy.models.url import Url
from musicbrainzpy.models.work import Work, WorkAttribute

__all__ = [
    "Alias",
    "Annotation",
    "Area",
    "AreaStub",
    "Artist",
    "ArtistCredit",
    "ArtistStub",
    "Collection",
    "Coordinates",
    "CoverArtArchive",
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
    "ReleaseGroupStub",
    "Series",
    "Tag",
    "TextRepresentation",
    "Track",
    "Url",
    "Work",
    "WorkAttribute",
]
