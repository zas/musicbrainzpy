"""Series model."""

from __future__ import annotations

from pydantic import Field

from musicbrainzpy.models.common import Alias, Genre, MBModel, Tag


class Series(MBModel):
    """A MusicBrainz series (release series, tour, etc.)."""

    id: str
    name: str
    disambiguation: str = ""
    type: str | None = None
    type_id: str | None = Field(default=None, alias="type-id")
    # Optional inc= fields
    aliases: list[Alias] | None = None
    tags: list[Tag] | None = None
    genres: list[Genre] | None = None
    annotation: str | None = None
