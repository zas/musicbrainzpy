"""Place model."""

from __future__ import annotations

from pydantic import Field

from musicbrainzpy.models.common import Alias, AreaStub, Genre, LifeSpan, MBModel, Tag


class Coordinates(MBModel):
    """Geographic coordinates."""

    latitude: float | None = None
    longitude: float | None = None


class Place(MBModel):
    """A MusicBrainz place (venue, studio, etc.)."""

    id: str
    name: str
    disambiguation: str = ""
    type: str | None = None
    type_id: str | None = Field(default=None, alias="type-id")
    address: str | None = None
    area: AreaStub | None = None
    coordinates: Coordinates | None = None
    life_span: LifeSpan | None = Field(default=None, alias="life-span")
    score: int | None = None  # search results only
    # Optional inc= fields
    aliases: list[Alias] | None = None
    tags: list[Tag] | None = None
    genres: list[Genre] | None = None
    annotation: str | None = None
