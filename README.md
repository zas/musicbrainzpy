# MusicBrainzPy

Modern Python bindings for the [MusicBrainz](https://musicbrainz.org/) JSON API.

Thin wrapper around the [MusicBrainz Web Service v2](https://musicbrainz.org/doc/MusicBrainz_API) — handles rate limiting, authentication, and (de)serialization via Pydantic models. All responses use the JSON API (`fmt=json`).

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
git clone https://github.com/zas/musicbrainzpy.git
cd musicbrainzpy
uv sync
```

## Usage

### Async client

```python
import asyncio
from musicbrainzpy import MusicBrainzClient

async def main():
    async with MusicBrainzClient("myapp", "1.0", "me@example.com") as client:
        # Search for an artist
        result = await client.search_typed("artist", "Metallica")
        artist = result.items[0]
        print(f"{artist.name} ({artist.country})")

        # Look up by MBID with includes
        artist = await client.lookup_typed("artist", artist.id, includes=["tags", "genres"])

        # Browse releases by artist
        releases = await client.browse_typed(
            "release", linked_type="artist", linked_id=artist.id, limit=10
        )
        for r in releases.items:
            print(f"  {r.title}")

asyncio.run(main())
```

### Sync client

```python
from musicbrainzpy import SyncMusicBrainzClient

with SyncMusicBrainzClient("myapp", "1.0", "me@example.com") as client:
    result = client.search_typed("artist", "Metallica")
    print(result.items[0].name)
```

### Raw dict responses

```python
# All typed methods have raw equivalents returning plain dicts:
data = await client.lookup("artist", mbid)
data = await client.search("artist", "Metallica")
data = await client.browse("release", linked_type="artist", linked_id=mbid)
```

### Non-MBID lookups

```python
recordings = await client.lookup_by_isrc("USEE10100063")
works = await client.lookup_by_iswc("T-070.116.274-5")
releases = await client.lookup_by_discid(discid, toc="1+12+267257+150")
```

### Submissions (require authentication)

```python
# Option 1: Digest auth
client = MusicBrainzClient("myapp", "1.0", "me@example.com",
                           username="user", password="pass")

# Option 2: OAuth2 (recommended)
from musicbrainzpy import OAuthHandler
oauth = OAuthHandler("client-id", "client-secret", "http://localhost:8080/callback")
await oauth.exchange_code("authorization-code")
client = MusicBrainzClient("myapp", "1.0", "me@example.com", oauth=oauth)

# Then submit
await client.submit_tags("myapp-1.0", {"artist": {mbid: ["rock", "metal"]}})
await client.submit_ratings("myapp-1.0", {"artist": {mbid: 80}})
```

See [docs/oauth2.md](docs/oauth2.md) for the full OAuth2 guide with PKCE, token refresh, and examples.

## Development

```bash
uv sync
uv run pytest tests/ -v
uv run ruff check .
uv run ruff format .
uv run ty check
```

## License

[GPL-3.0-or-later](LICENSE)
