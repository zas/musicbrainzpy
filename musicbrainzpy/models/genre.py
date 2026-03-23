"""Genre model."""

from __future__ import annotations

from musicbrainzpy.models.common import MBModel


class GenreFull(MBModel):
    """A MusicBrainz genre (from /genre/ endpoint)."""

    id: str
    name: str
    disambiguation: str = ""
