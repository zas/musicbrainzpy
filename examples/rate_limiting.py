"""Demonstrate that the async rate limiter yields control between API calls.

The MusicBrainz API requires max 1 request/second. Because the rate limiter
uses asyncio.sleep(), other tasks can run during the wait. This example
shows a background task making progress while API calls are rate-limited.
"""

from __future__ import annotations

import asyncio
import time

from musicbrainzpy import MusicBrainzClient


async def background_work() -> None:
    """Simulate background processing that runs between API calls."""
    i = 0
    while True:
        i += 1
        print(f"  [background] doing work #{i}")
        await asyncio.sleep(0.3)


async def main() -> None:
    start = time.monotonic()

    def elapsed() -> str:
        return f"{time.monotonic() - start:.1f}s"

    async with MusicBrainzClient("musicbrainzpy-examples", "0.1.0", "you@example.com") as mb:
        # Start background work alongside API calls
        bg = asyncio.create_task(background_work())

        artists = ["Metallica", "Reverend Bizarre", "Candlemass"]
        for name in artists:
            print(f"[{elapsed()}] Searching for {name}...")
            result = await mb.search("artist", f'artist:"{name}"', limit=1)
            artist = result["artists"][0]
            print(f"[{elapsed()}] Found: {artist['name']} ({artist.get('country', '?')})")

        bg.cancel()

    print(f"\n3 API calls completed in {elapsed()} (rate limited to 1 req/s)")
    print("Background work ran during the waits — no time wasted!")


if __name__ == "__main__":
    asyncio.run(main())
