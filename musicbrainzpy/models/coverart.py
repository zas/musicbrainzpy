"""Cover Art Archive models."""

from __future__ import annotations

from pydantic import Field

from musicbrainzpy.models.common import MBModel


class Thumbnails(MBModel):
    """Thumbnail URLs for a cover art image."""

    small: str | None = None
    large: str | None = None
    t250: str | None = Field(default=None, alias="250")
    t500: str | None = Field(default=None, alias="500")
    t1200: str | None = Field(default=None, alias="1200")


class CoverArtImage(MBModel):
    """A single cover art image entry."""

    id: str
    types: list[str] = Field(default_factory=list)
    front: bool = False
    back: bool = False
    image: str
    thumbnails: Thumbnails
    comment: str = ""
    approved: bool = False
    edit: int | None = None


class CoverArtImageList(MBModel):
    """JSON listing of cover art for a release or release group."""

    images: list[CoverArtImage] = Field(default_factory=list)
    release: str
