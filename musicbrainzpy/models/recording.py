"""Recording model."""

from __future__ import annotations

from pydantic import Field

from musicbrainzpy.models.common import Alias, ArtistCredit, Genre, MBModel, Rating, Tag


class Recording(MBModel):
    """A MusicBrainz recording."""

    id: str
    title: str
    disambiguation: str = ""
    length: int | None = None
    video: bool | None = None
    first_release_date: str | None = Field(default=None, alias="first-release-date")
    artist_credit: list[ArtistCredit] | None = Field(default=None, alias="artist-credit")
    isrcs: list[str] | None = None
    score: int | None = None  # search results only
    artist_credit_id: str | None = Field(default=None, alias="artist-credit-id")  # search results only
    # Optional inc= fields
    aliases: list[Alias] | None = None
    releases: list[MBModel] | None = None  # avoids circular import with Release
    tags: list[Tag] | None = None
    genres: list[Genre] | None = None
    rating: Rating | None = None
    annotation: str | None = None
