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
        # get_collections() returns the authenticated user's collections
        # (both public and private).
        collections = await mb.get_collections()
        print(f"\nCollections for {username} ({len(collections)} total):\n")

        for coll in collections:
            print(f"  {coll.name} ({coll.entity_type})")

            # Browse the first 5 items in each collection.
            result = await mb.browse_typed(coll.entity_type, linked_type="collection", linked_id=coll.id, limit=5)
            if not result.items:
                print("    (empty)")
            for item in result.items:
                label = getattr(item, "title", None) or getattr(item, "name", None) or str(item)
                print(f"    - {label}")
            if result.count > 5:
                print(f"    ... and {result.count - 5} more")
            print()

        # Submit a tag — digest auth is sent automatically.
        # Uncomment to try (will raise AuthenticationError with wrong password):
        # try:
        #     await mb.submit_tags(
        #         {"artist": {"30bbf75a-62d4-4d43-862b-91a224a0eb67": ["doom metal"]}},
        #     )
        #     print("\nTag submitted!")
        # except AuthenticationError:
        #     print("\nTag submission failed: bad credentials.")


if __name__ == "__main__":
    asyncio.run(main())
