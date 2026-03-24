"""Shared Pydantic models used across entity types."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("musicbrainzpy")


class MBModel(BaseModel):
    """Base model for all MusicBrainz entities. Allows extra fields for forward compatibility."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def model_post_init(self, __context: Any) -> None:
        if self.model_extra:
            logger.debug("Unmapped fields on %s: %s", type(self).__name__, list(self.model_extra.keys()))


class LifeSpan(MBModel):
    """A begin/end date range."""

    begin: str | None = None
    end: str | None = None
    ended: bool | None = None


class AreaStub(MBModel):
    """Minimal area reference embedded in other entities."""

    id: str
    name: str
    sort_name: str = Field(alias="sort-name")
    disambiguation: str = ""
    type: str | None = None
    type_id: str | None = Field(default=None, alias="type-id")
    life_span: LifeSpan | None = Field(default=None, alias="life-span")
    iso_3166_1_codes: list[str] = Field(default_factory=list, alias="iso-3166-1-codes")
    iso_3166_2_codes: list[str] = Field(default_factory=list, alias="iso-3166-2-codes")


class Tag(MBModel):
    """A user-submitted tag with vote count."""

    name: str
    count: int = 0


class Genre(MBModel):
    """A genre tag with vote count."""

    id: str
    name: str
    count: int = 0
    disambiguation: str = ""


class Rating(MBModel):
    """Aggregate rating."""

    value: float | None = None
    votes_count: int = Field(default=0, alias="votes-count")


class Alias(MBModel):
    """An alternative name for an entity."""

    name: str
    sort_name: str = Field(alias="sort-name")
    type: str | None = None
    type_id: str | None = Field(default=None, alias="type-id")
    locale: str | None = None
    primary: bool | None = None
    begin: str | None = None
    end: str | None = None
    ended: bool | None = None
    # Search API uses begin-date/end-date instead of begin/end
    begin_date: str | None = Field(default=None, alias="begin-date")
    end_date: str | None = Field(default=None, alias="end-date")


class ArtistStub(MBModel):
    """Minimal artist reference embedded in artist credits."""

    id: str
    name: str
    sort_name: str = Field(alias="sort-name")
    disambiguation: str = ""
    type: str | None = None
    type_id: str | None = Field(default=None, alias="type-id")
    country: str | None = None
    aliases: list[Alias] | None = None
    tags: list[Tag] | None = None
    genres: list[Genre] | None = None


class ArtistCredit(MBModel):
    """An artist credit entry (artist + join phrase)."""

    name: str = ""
    artist: ArtistStub
    joinphrase: str = ""


class TextRepresentation(MBModel):
    """Language and script of a release."""

    language: str | None = None
    script: str | None = None


class ReleaseEvent(MBModel):
    """A release event (date + area)."""

    date: str | None = None
    area: AreaStub | None = None
