"""Recording model."""

from __future__ import annotations

from pydantic import Field

from musicbrainzpy.models.common import ArtistCredit, Genre, MBModel, Rating, Tag


class Recording(MBModel):
    """A MusicBrainz recording."""

    id: str
    title: str
    disambiguation: str = ""
    length: int | None = None
    video: bool = False
    first_release_date: str | None = Field(default=None, alias="first-release-date")
    artist_credit: list[ArtistCredit] | None = Field(default=None, alias="artist-credit")
    isrcs: list[str] | None = None
    # Optional inc= fields
    tags: list[Tag] | None = None
    genres: list[Genre] | None = None
    rating: Rating | None = None
    annotation: str | None = None
