# MusicBrainzPy

Modern Python bindings for the [MusicBrainz](https://musicbrainz.org/) JSON API.

Thin wrapper around the [MusicBrainz Web Service v2](https://musicbrainz.org/doc/MusicBrainz_API) — handles rate limiting, authentication, and (de)serialization via Pydantic models. All responses use the JSON API (`Accept: application/json`).

## Why musicbrainzpy over musicbrainzngs?

| | musicbrainzngs | musicbrainzpy |
|---|---|---|
| API format | XML (parsed to dicts) | JSON (native) |
| Return types | Plain dicts with `-list` suffixes | Pydantic models with IDE autocompletion |
| Architecture | Global module state | Instance-based clients |
| Async | No | Yes (+ sync client) |
| Auth | Digest only | Digest + OAuth2 (PKCE, refresh, revoke) |
| Error handling | Generic exceptions | Typed exceptions + automatic retry with backoff |
| Maintenance | Inactive since 2023 | Active |
| Entity coverage | Missing newer entities/fields | All 13 entity types, forward-compatible with new API fields |
| Python | 2.7+ | 3.10+ |
| HTTP | urllib | httpx (connection pooling, HTTP/2, timeouts) |
| Cover Art Archive | Raw bytes only | Typed client with image listings and metadata |

Key improvements:

- **One method instead of dozens** — `lookup_typed("artist", mbid)` replaces `get_artist_by_id`, `get_release_by_id`, `get_recording_by_id`, etc.
- **Lucene queries directly** — no leaky abstraction that builds queries from kwargs
- **Multiple clients** — different configs, auth, rate limits running concurrently without conflicts
- **Resilient** — automatic retry on transient failures (connection errors, 429/503), respects `Retry-After`
- **Zero-config** — set `MUSICBRAINZPY_*` env vars once, construct clients with no arguments

Coming from musicbrainzngs? See the [migration guide](docs/migrating-from-ngs.md).

## Requirements

- Python 3.10+
- [httpx](https://www.python-httpx.org/) ≥ 0.28
- [Pydantic](https://docs.pydantic.dev/) ≥ 2.10

## Installation

As a dependency in another project:

```bash
uv add "musicbrainzpy @ git+https://github.com/zas/musicbrainzpy.git"
```

From source:

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
data = await client.lookup_by_url("https://www.metallica.com/")
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
await client.submit_barcodes("myapp-1.0", {release_mbid: "4050538793819"})
await client.submit_isrcs("myapp-1.0", {recording_mbid: ["USEE10100063"]})

# Collection management
await client.collection_add("myapp-1.0", collection_mbid, "releases", [mbid])
await client.collection_remove("myapp-1.0", collection_mbid, "releases", [mbid])
```

### Cover Art Archive

```python
from musicbrainzpy import SyncCoverArtClient

with SyncCoverArtClient("myapp", "1.0", "me@example.com") as caa:
    # List images for a release
    image_list = caa.get_image_list(release_mbid)
    for img in image_list.images:
        print(f"  {img.id}: {img.types} ({img.front=})")

    # Download front cover (full-size or thumbnail)
    data = caa.get_front(release_mbid)
    data = caa.get_front(release_mbid, size=500)  # 250, 500, or 1200

    # Get image metadata without downloading
    info = caa.image_info(release_mbid, "front")
    print(f"  {info['content_type']}, {info['content_length']} bytes")
```

Async version: `CoverArtClient` with the same methods (all `await`-able).

### Annotation helpers

```python
from musicbrainzpy import annotation_to_text, annotation_to_markdown

# Convert MusicBrainz wiki markup to plain text or Markdown
plain = annotation_to_text(artist.annotation)
md = annotation_to_markdown(artist.annotation)
```

### Environment variables

Client defaults can be set via environment variables (explicit constructor args always win):

| Variable | Overrides |
|---|---|
| `MUSICBRAINZPY_APP` | `app_name` |
| `MUSICBRAINZPY_VERSION` | `app_version` |
| `MUSICBRAINZPY_CONTACT` | `app_contact` |
| `MUSICBRAINZPY_BASE_URL` | `base_url` |
| `MUSICBRAINZPY_USERNAME` | `username` |
| `MUSICBRAINZPY_PASSWORD` | `password` |

```bash
export MUSICBRAINZPY_APP=myapp
export MUSICBRAINZPY_VERSION=1.0
export MUSICBRAINZPY_CONTACT=me@example.com
```

```python
# No args needed when env vars are set
client = SyncMusicBrainzClient()
```

See [docs/oauth2.md](docs/oauth2.md) for the full OAuth2 guide with PKCE, token refresh, and examples.

More examples in the [examples/](examples/) directory:

```bash
uv run python examples/search_artists.py
uv run python examples/cover_art.py
```

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
