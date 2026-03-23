"""Release model."""

from __future__ import annotations

from pydantic import Field

from musicbrainzpy.models.common import (
    ArtistCredit,
    Genre,
    MBModel,
    ReleaseEvent,
    Tag,
    TextRepresentation,
)


class Track(MBModel):
    """A track on a medium."""

    id: str
    title: str
    number: str = ""
    position: int = 0
    length: int | None = None


class Medium(MBModel):
    """A medium (disc) within a release."""

    position: int = 0
    format: str | None = None
    format_id: str | None = Field(default=None, alias="format-id")
    track_count: int = Field(default=0, alias="track-count")
    tracks: list[Track] | None = None


class LabelInfo(MBModel):
    """Label and catalog number for a release."""

    catalog_number: str | None = Field(default=None, alias="catalog-number")
    label: LabelStub | None = None


class LabelStub(MBModel):
    """Minimal label reference."""

    id: str
    name: str
    disambiguation: str = ""


# Rebuild LabelInfo now that LabelStub is defined
LabelInfo.model_rebuild()


class Release(MBModel):
    """A MusicBrainz release (specific edition)."""

    id: str
    title: str
    disambiguation: str = ""
    status: str | None = None
    status_id: str | None = Field(default=None, alias="status-id")
    date: str | None = None
    country: str | None = None
    barcode: str | None = None
    packaging: str | None = None
    packaging_id: str | None = Field(default=None, alias="packaging-id")
    quality: str | None = None
    text_representation: TextRepresentation | None = Field(default=None, alias="text-representation")
    artist_credit: list[ArtistCredit] | None = Field(default=None, alias="artist-credit")
    release_events: list[ReleaseEvent] | None = Field(default=None, alias="release-events")
    media: list[Medium] | None = None
    label_info: list[LabelInfo] | None = Field(default=None, alias="label-info")
    # Optional inc= fields
    tags: list[Tag] | None = None
    genres: list[Genre] | None = None
