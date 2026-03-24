"""Retrieve cover art for a release (Sufjan Stevens — Carrie & Lowell, 2xCD)."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from musicbrainzpy import CoverArtClient, MusicBrainzClient

RELEASE_ID = "de8231d3-b745-42fa-9e0c-7ffb6d3d9608"


async def main() -> None:
    async with MusicBrainzClient("musicbrainzpy-examples", "0.1.0", "you@example.com") as mb:
        release = await mb.lookup_typed("release", RELEASE_ID, includes=["artist-credits"])
        print(f"Release: {release.title} (id: {release.id})")  # type: ignore[attr-defined]

    async with CoverArtClient("musicbrainzpy-examples", "0.1.0", "you@example.com") as caa:
        # Download the 250px front cover
        front = await caa.get_front(RELEASE_ID, size=250)
        out = Path(tempfile.gettempdir()) / "front-250.jpg"
        out.write_bytes(front)
        print(f"\nFront cover saved to {out.resolve()} ({len(front)} bytes)")

        # List all available cover art images with full-size metadata
        listing = await caa.get_image_list(RELEASE_ID)
        print(f"\nAvailable cover art ({len(listing.images)} images):\n")
        for img in listing.images:
            info = await caa.image_info(RELEASE_ID, str(img.id))
            content_type = info["content_type"] or "?"
            size_bytes = info["content_length"]
            size_str = f"{int(size_bytes) / 1024:.0f} KB" if size_bytes else "?"
            thumbs = []
            if img.thumbnails.t250:
                thumbs.append("250px")
            if img.thumbnails.t500:
                thumbs.append("500px")
            if img.thumbnails.t1200:
                thumbs.append("1200px")
            types = ", ".join(img.types) or "untyped"
            comment = f'  "{img.comment}"' if img.comment else ""
            print(f"  [{img.id}] {types}")
            print(f"    {content_type}, {size_str}, thumbnails: {', '.join(thumbs)}{comment}")


if __name__ == "__main__":
    asyncio.run(main())
