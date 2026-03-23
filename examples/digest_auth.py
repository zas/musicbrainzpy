"""List your private collections using digest (username/password) authentication."""

from __future__ import annotations

import asyncio
import getpass

from musicbrainzpy import AuthenticationError, MusicBrainzClient


async def main() -> None:
    username = input("MusicBrainz username: ")
    password = getpass.getpass("MusicBrainz password: ")

    async with MusicBrainzClient(
        "musicbrainzpy-examples",
        "0.1.0",
        "you@example.com",
        username=username,
        password=password,
    ) as mb:
        try:
            # List all collections (including private ones, thanks to auth)
            data = await mb.browse("collection", linked_type="editor", linked_id=username)
        except AuthenticationError:
            print("Authentication failed. Check your username and password.")
            return

        print(f"\nCollections for {username} ({data['collection-count']} total):\n")
        for c in data["collections"]:
            entity = c["entity-type"]
            count = c.get(f"{entity}-count", 0)
            print(f"  {c['name']} ({entity}, {count} items)")


if __name__ == "__main__":
    asyncio.run(main())
