"""Work model."""

from __future__ import annotations

from pydantic import Field

from musicbrainzpy.models.common import Alias, Genre, MBModel, Rating, Tag


class Work(MBModel):
    """A MusicBrainz work (composition)."""

    id: str
    title: str
    disambiguation: str = ""
    type: str | None = None
    type_id: str | None = Field(default=None, alias="type-id")
    language: str | None = None
    languages: list[str] = Field(default_factory=list)
    iswcs: list[str] = Field(default_factory=list)
    # Optional inc= fields
    aliases: list[Alias] | None = None
    tags: list[Tag] | None = None
    genres: list[Genre] | None = None
    rating: Rating | None = None
