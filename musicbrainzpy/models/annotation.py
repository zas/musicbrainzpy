"""Annotation model."""

from __future__ import annotations

from musicbrainzpy.models.common import MBModel


class Annotation(MBModel):
    """A MusicBrainz annotation search result."""

    type: str
    score: int = 0
    entity: str
    name: str
    text: str = ""
