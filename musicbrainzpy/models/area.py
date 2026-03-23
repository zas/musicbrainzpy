"""Area model."""

from __future__ import annotations

from pydantic import Field

from musicbrainzpy.models.common import Alias, Genre, LifeSpan, MBModel, Tag


class Area(MBModel):
    """A MusicBrainz area (country, city, etc.)."""

    id: str
    name: str
    sort_name: str = Field(alias="sort-name")
    disambiguation: str = ""
    type: str | None = None
    type_id: str | None = Field(default=None, alias="type-id")
    iso_3166_1_codes: list[str] = Field(default_factory=list, alias="iso-3166-1-codes")
    iso_3166_2_codes: list[str] = Field(default_factory=list, alias="iso-3166-2-codes")
    iso_3166_3_codes: list[str] = Field(default_factory=list, alias="iso-3166-3-codes")
    life_span: LifeSpan | None = Field(default=None, alias="life-span")
    # Optional inc= fields
    aliases: list[Alias] | None = None
    tags: list[Tag] | None = None
    genres: list[Genre] | None = None
    annotation: str | None = None
