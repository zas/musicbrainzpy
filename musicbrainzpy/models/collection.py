"""Collection model."""

from __future__ import annotations

from pydantic import Field

from musicbrainzpy.models.common import MBModel


class Collection(MBModel):
    """A MusicBrainz collection."""

    id: str
    name: str
    editor: str
    type: str | None = None
    type_id: str | None = Field(default=None, alias="type-id")
    entity_type: str = Field(alias="entity-type")
