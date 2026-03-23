"""Fetch and display the discography of Reverend Bizarre."""

from __future__ import annotations

import asyncio

from musicbrainzpy import MusicBrainzClient


async def main() -> None:
    async with MusicBrainzClient("musicbrainzpy-examples", "0.1.0", "you@example.com") as mb:
        # Search for the artist
        result = await mb.search("artist", 'artist:"Reverend Bizarre"', limit=1)
        artist = result["artists"][0]
        artist_id = artist["id"]
        print(f"{artist['name']} ({artist['country']})\n")

        # Browse all release groups (albums, EPs, singles, etc.)
        offset = 0
        while True:
            page = await mb.browse("release-group", linked_type="artist", linked_id=artist_id, limit=100, offset=offset)
            for rg in page["release-groups"]:
                primary = rg.get("primary-type", "")
                secondary = ", ".join(rg.get("secondary-types", []))
                rg_type = f"{primary} + {secondary}" if secondary else primary
                print(f"  [{rg_type}] {rg['title']} ({rg.get('first-release-date', '?')})")

            total = page["release-group-count"]
            offset += len(page["release-groups"])
            if offset >= total:
                break

        print(f"\nTotal: {total} release groups")


if __name__ == "__main__":
    asyncio.run(main())
