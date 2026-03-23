"""Release group model."""

from __future__ import annotations

from pydantic import Field

from musicbrainzpy.models.common import ArtistCredit, Genre, MBModel, Rating, Tag
from musicbrainzpy.models.release import Release


class ReleaseGroup(MBModel):
    """A MusicBrainz release group (album concept)."""

    id: str
    title: str
    disambiguation: str = ""
    primary_type: str | None = Field(default=None, alias="primary-type")
    primary_type_id: str | None = Field(default=None, alias="primary-type-id")
    secondary_types: list[str] = Field(default_factory=list, alias="secondary-types")
    secondary_type_ids: list[str] = Field(default_factory=list, alias="secondary-type-ids")
    first_release_date: str | None = Field(default=None, alias="first-release-date")
    artist_credit: list[ArtistCredit] | None = Field(default=None, alias="artist-credit")
    # Optional inc= fields
    releases: list[Release] | None = None
    tags: list[Tag] | None = None
    genres: list[Genre] | None = None
    rating: Rating | None = None
    annotation: str | None = None
