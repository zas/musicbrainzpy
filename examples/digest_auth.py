"""List your collections (including private) using digest authentication."""

from __future__ import annotations

import asyncio
import getpass

from musicbrainzpy import AuthenticationError, MusicBrainzClient  # noqa: F401


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
        # inc=user-collections is required to include private collections;
        # without it, only public collections are returned.
        data = await mb.browse("collection", linked_type="editor", linked_id=username, includes=["user-collections"])
        print(f"\nCollections for {username} ({data['collection-count']} total):\n")
        for c in data["collections"]:
            entity = c["entity-type"]
            count = c.get(f"{entity}-count", 0)
            print(f"  {c['name']} ({entity}, {count} items)")

        # Submit a tag — digest auth is sent automatically.
        # Uncomment to try (will raise AuthenticationError with wrong password):
        # try:
        #     await mb.submit_tags(
        #         "musicbrainzpy-examples-0.1.0",
        #         {"artist": {"30bbf75a-62d4-4d43-862b-91a224a0eb67": ["doom metal"]}},
        #     )
        #     print("\nTag submitted!")
        # except AuthenticationError:
        #     print("\nTag submission failed: bad credentials.")


if __name__ == "__main__":
    asyncio.run(main())
