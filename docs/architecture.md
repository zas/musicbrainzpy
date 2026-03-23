# MusicBrainzPy Architecture & Specifications

## Overview

MusicBrainzPy is a thin Python wrapper around the MusicBrainz JSON API (Web Service v2).
It handles the plumbing (rate limiting, User-Agent, auth, serialization) and exposes
typed Pydantic models for all 13 core entity types.

## Design Principles

- **Thin wrapper**: no business logic beyond what the API provides
- **JSON-native**: uses `fmt=json` for all GET requests; submissions use XML (API requirement)
- **Async-first**: built on `httpx.AsyncClient`; sync wrapper provided for convenience
- **Typed**: Pydantic v2 models with `extra="allow"` for forward compatibility
- **Minimal dependencies**: `httpx` + `pydantic` only

## API Coverage

### Three request types (GET)

| Type   | URL pattern                                              | Description                          |
|--------|----------------------------------------------------------|--------------------------------------|
| Lookup | `/<entity>/<mbid>?inc=<INC>`                             | Fetch a single entity by MBID        |
| Browse | `/<entity>?<linked_type>=<mbid>&limit=&offset=&inc=`     | List entities linked to another      |
| Search | `/<entity>?query=<query>&limit=&offset=`                 | Full-text search                     |

### Non-MBID lookups (GET)

| Resource | URL pattern                    | Returns          |
|----------|--------------------------------|------------------|
| ISRC     | `/isrc/<isrc>`                 | List of recordings |
| ISWC     | `/iswc/<iswc>`                 | List of works     |
| Disc ID  | `/discid/<discid>?toc=<toc>`   | List of releases  |
| URL      | `/url?resource=<url>`          | URL entity        |

### Submissions (POST/PUT/DELETE — XML only)

| Endpoint                              | Method     | Description              |
|---------------------------------------|------------|--------------------------|
| `/ws/2/tag`                           | POST       | Submit tags/genres       |
| `/ws/2/rating`                        | POST       | Submit ratings           |
| `/ws/2/release/`                      | POST       | Submit barcodes          |
| `/ws/2/recording/`                    | POST       | Submit ISRCs             |
| `/ws/2/collection/<id>/<type>/<ids>`  | PUT/DELETE  | Manage collections       |

All submissions require authentication and a `client=` parameter.

## Core Entities (13)

`area`, `artist`, `event`, `genre`, `instrument`, `label`, `place`,
`recording`, `release`, `release-group`, `series`, `work`, `url`

## Base URL

Default (HTTPS):

    https://musicbrainz.org/ws/2/

The base URL is configurable via the client constructor to support mirrors and local instances.

## Rate Limiting

- Max 1 request per second (API requirement)
- Implemented as a simple timestamp check with `asyncio.sleep()`

## Authentication

- Digest auth (via `httpx.DigestAuth`) — current standard
- OAuth2 — for user-scoped operations (tags, ratings, collections)

## Module Layout

```
musicbrainzpy/
├── __init__.py          # Public API re-exports
├── client.py            # MusicBrainzClient (async + sync)
├── models/              # Pydantic models per entity type
│   ├── __init__.py      # Re-exports all models
│   ├── common.py        # Shared: ArtistCredit, LifeSpan, Tag, Relation, etc.
│   ├── artist.py
│   ├── release.py
│   ├── recording.py
│   ├── release_group.py
│   ├── label.py
│   ├── work.py
│   ├── area.py
│   ├── event.py
│   ├── place.py
│   ├── instrument.py
│   ├── series.py
│   ├── genre.py
│   └── url.py
├── enums.py             # EntityType, ReleaseStatus, ReleaseGroupType, etc.
├── auth.py              # OAuth2 flow helpers
├── exceptions.py        # MusicBrainzError, NotFoundError, RateLimitedError, etc.
└── _ratelimit.py        # Async/sync rate limiter
tests/
├── conftest.py          # respx fixtures, sample JSON responses
├── test_client.py       # Lookup/browse/search integration tests
└── test_models.py       # Deserialization round-trip tests
```

## Implementation Order

1. Project scaffolding (pyproject.toml, structure)
2. Enums, exceptions, rate limiter
3. Client core — raw lookup/browse/search returning dicts
4. Pydantic models — common.py first, then entity by entity
5. Typed convenience methods on client
6. Non-MBID lookups (ISRC, ISWC, disc ID, URL)
7. Auth (digest + OAuth2)
8. Submissions (XML body builder via stdlib xml.etree.ElementTree)
9. Sync wrapper
10. Docs, examples, packaging
