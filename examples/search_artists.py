"""Search for artists from Paris, France, formed in 2020."""

from __future__ import annotations

import asyncio

from musicbrainzpy import MusicBrainzClient


async def main() -> None:
    async with MusicBrainzClient("musicbrainzpy-examples", "0.1.0", "you@example.com") as mb:
        result = await mb.search(
            "artist",
            'beginarea:"Paris" AND country:FR AND begin:2020',
            limit=25,
        )
        artists = result["artists"]
        print(f"Artists from Paris, France — formed in 2020 ({result['count']} total):\n")
        for a in artists:
            life = a.get("life-span", {})
            begin = life.get("begin", "?")
            a_type = a.get("type", "?")
            print(f"  {a['name']} ({a_type}, formed {begin})")


if __name__ == "__main__":
    asyncio.run(main())
