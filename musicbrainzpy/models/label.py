"""Label model."""

from __future__ import annotations

from pydantic import Field

from musicbrainzpy.models.common import (
    Alias,
    AreaStub,
    Genre,
    LifeSpan,
    MBModel,
    Rating,
    Tag,
)


class Label(MBModel):
    """A MusicBrainz label."""

    id: str
    name: str
    sort_name: str = Field(alias="sort-name")
    disambiguation: str = ""
    type: str | None = None
    type_id: str | None = Field(default=None, alias="type-id")
    label_code: int | None = Field(default=None, alias="label-code")
    country: str | None = None
    area: AreaStub | None = None
    life_span: LifeSpan | None = Field(default=None, alias="life-span")
    ipis: list[str] = Field(default_factory=list)
    isnis: list[str] = Field(default_factory=list)
    # Optional inc= fields
    aliases: list[Alias] | None = None
    tags: list[Tag] | None = None
    genres: list[Genre] | None = None
    rating: Rating | None = None
    annotation: str | None = None
