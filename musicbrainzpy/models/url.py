"""URL model."""

from __future__ import annotations

from musicbrainzpy.models.common import MBModel


class Url(MBModel):
    """A MusicBrainz URL entity."""

    id: str
    resource: str
