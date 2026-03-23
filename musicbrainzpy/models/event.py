"""Event model."""

from __future__ import annotations

from pydantic import Field

from musicbrainzpy.models.common import Alias, Genre, LifeSpan, MBModel, Rating, Tag


class Event(MBModel):
    """A MusicBrainz event (concert, festival, etc.)."""

    id: str
    name: str
    disambiguation: str = ""
    type: str | None = None
    type_id: str | None = Field(default=None, alias="type-id")
    cancelled: bool = False
    life_span: LifeSpan | None = Field(default=None, alias="life-span")
    time: str | None = None
    setlist: str | None = None
    # Optional inc= fields
    aliases: list[Alias] | None = None
    tags: list[Tag] | None = None
    genres: list[Genre] | None = None
    rating: Rating | None = None
