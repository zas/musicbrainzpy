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
from musicbrainzpy.models.recording import Recording as RecordingModel


class Track(MBModel):
    """A track on a medium."""

    id: str
    title: str
    number: str = ""
    position: int = 0
    length: int | None = None
    artist_credit: list[ArtistCredit] | None = Field(default=None, alias="artist-credit")
    recording: RecordingModel | None = None


class Medium(MBModel):
    """A medium (disc) within a release."""

    position: int = 0
    title: str = ""
    format: str | None = None
    format_id: str | None = Field(default=None, alias="format-id")
    track_count: int = Field(default=0, alias="track-count")
    track_offset: int = Field(default=0, alias="track-offset")
    disc_count: int = Field(default=0, alias="disc-count")
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


class CoverArtArchive(MBModel):
    """Cover Art Archive availability info."""

    artwork: bool = False
    front: bool = False
    back: bool = False
    count: int = 0
    darkened: bool = False


class ReleaseGroupStub(MBModel):
    """Minimal release group reference embedded in releases."""

    id: str
    title: str = ""
    disambiguation: str = ""
    primary_type: str | None = Field(default=None, alias="primary-type")
    primary_type_id: str | None = Field(default=None, alias="primary-type-id")
    secondary_types: list[str] = Field(default_factory=list, alias="secondary-types")
    secondary_type_ids: list[str] = Field(default_factory=list, alias="secondary-type-ids")


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
    asin: str | None = None
    packaging: str | None = None
    packaging_id: str | None = Field(default=None, alias="packaging-id")
    quality: str | None = None
    text_representation: TextRepresentation | None = Field(default=None, alias="text-representation")
    artist_credit: list[ArtistCredit] | None = Field(default=None, alias="artist-credit")
    release_group: ReleaseGroupStub | None = Field(default=None, alias="release-group")
    release_events: list[ReleaseEvent] | None = Field(default=None, alias="release-events")
    media: list[Medium] | None = None
    label_info: list[LabelInfo] | None = Field(default=None, alias="label-info")
    cover_art_archive: CoverArtArchive | None = Field(default=None, alias="cover-art-archive")
    # Optional inc= fields
    tags: list[Tag] | None = None
    genres: list[Genre] | None = None
    annotation: str | None = None
