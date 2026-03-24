"""Artist model."""

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
from musicbrainzpy.models.recording import Recording
from musicbrainzpy.models.release import Release
from musicbrainzpy.models.release_group import ReleaseGroup
from musicbrainzpy.models.work import Work


class Artist(MBModel):
    """A MusicBrainz artist."""

    id: str
    name: str
    sort_name: str = Field(alias="sort-name")
    disambiguation: str = ""
    type: str | None = None
    type_id: str | None = Field(default=None, alias="type-id")
    gender: str | None = None
    gender_id: str | None = Field(default=None, alias="gender-id")
    country: str | None = None
    area: AreaStub | None = None
    begin_area: AreaStub | None = Field(default=None, alias="begin-area")
    end_area: AreaStub | None = Field(default=None, alias="end-area")
    life_span: LifeSpan | None = Field(default=None, alias="life-span")
    ipis: list[str] = Field(default_factory=list)
    isnis: list[str] = Field(default_factory=list)
    score: int | None = None  # search results only
    # Optional inc= fields
    aliases: list[Alias] | None = None
    tags: list[Tag] | None = None
    genres: list[Genre] | None = None
    rating: Rating | None = None
    annotation: str | None = None
    releases: list[Release] | None = None
    release_groups: list[ReleaseGroup] | None = Field(default=None, alias="release-groups")
    recordings: list[Recording] | None = None
    works: list[Work] | None = None
