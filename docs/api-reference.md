# MusicBrainz JSON API Reference

Source: https://musicbrainz.org/doc/MusicBrainz_API

## Base URL

    https://musicbrainz.org/ws/2/

All requests set the `Accept: application/json` header.

## Rate Limiting

- Max 1 request/second per client
- Must set a meaningful `User-Agent` header: `AppName/Version ( contact-url-or-email )`
- Violators get IP-blocked
- Server returns HTTP 503 (or 429) when rate limit is exceeded

## Retry Behavior

All clients automatically retry on transient failures:

- **Retried**: `httpx.TransportError` (connection errors, timeouts), HTTP 429, HTTP 503
- **Not retried**: HTTP 400, 401, 404, or any other client/server error
- **Default**: 3 retries with exponential backoff (1s, 2s, 4s)
- **Retry-After**: respected when the server includes the header
- **Configuration**: `max_retries=` and `retry_base_delay=` constructor params; set `max_retries=0` to disable

## Lookup

    GET /<entity_type>/<mbid>?inc=<INC>

### Subqueries (inc=)

| Entity         | Available inc= subqueries                              |
|----------------|---------------------------------------------------------|
| artist         | recordings, releases, release-groups, works             |
| label          | releases                                                |
| recording      | releases, release-groups                                |
| release        | collections, labels, recordings, release-groups         |
| release-group  | releases                                                |

Subquery results limited to 25; use browse for the rest.

### Additional inc= modifiers

- `discids`, `media`, `isrcs`, `artist-credits`, `various-artists`
- `aliases`, `annotation`
- `tags`, `ratings`, `genres` (and `user-tags`, `user-ratings`, `user-genres` with auth)

### Relationship inc= values

`area-rels`, `artist-rels`, `event-rels`, `genre-rels`, `instrument-rels`,
`label-rels`, `place-rels`, `recording-rels`, `release-rels`, `release-group-rels`,
`series-rels`, `url-rels`, `work-rels`

Plus for releases: `recording-level-rels`, `release-group-level-rels`, `work-level-rels`

## Browse

    GET /<entity_type>?<linked_type>=<mbid>&limit=<N>&offset=<N>&inc=<INC>

- Default limit: 25, max: 100
- Paging via `offset=`
- Releases capped at 500 tracks per page
- Filterable by `type=` and `status=`

### Linked entities

| Browse for      | By                                                                          |
|-----------------|-----------------------------------------------------------------------------|
| area            | collection                                                                  |
| artist          | area, collection, recording, release, release-group, work                   |
| event           | area, artist, collection, event, place                                      |
| label           | area, collection, release                                                   |
| place           | area, collection                                                            |
| recording       | artist, collection, release, work                                           |
| release         | area, artist, collection, label, track, track_artist, recording, release-group |
| release-group   | artist, collection, release                                                 |
| series          | collection                                                                  |
| work            | artist, collection                                                          |

### Browse inc= values

| Entity         | inc=                                                        |
|----------------|-------------------------------------------------------------|
| recording      | artist-credits, isrcs                                       |
| release        | artist-credits, labels, recordings, release-groups, media, discids, isrcs |
| release-group  | artist-credits                                              |
| others         | aliases                                                     |

All entities also support: `annotation`, `tags`, `genres`, `ratings` (except area, place, release, series for ratings).

## Search

    GET /<entity_type>?query=<QUERY>&limit=<N>&offset=<N>

Search syntax documented at: https://musicbrainz.org/doc/MusicBrainz_API/Search

## Non-MBID Lookups

| Path                        | Returns            | Notes                              |
|-----------------------------|--------------------|------------------------------------|
| `/isrc/<isrc>`              | List of recordings | inc= same as recording lookup      |
| `/iswc/<iswc>`              | List of works      | inc= same as work lookup           |
| `/discid/<discid>?toc=<T>`  | List of releases   | Supports fuzzy TOC matching        |
| `/url?resource=<url>`       | URL entity         | Up to 100 URLs per request         |

## Submissions (XML only, require auth)

| Endpoint                              | Method     | Content-Type              |
|---------------------------------------|------------|---------------------------|
| `/ws/2/tag?client=<C>`                | POST       | application/xml           |
| `/ws/2/rating?client=<C>`             | POST       | application/xml           |
| `/ws/2/release/?client=<C>`           | POST       | application/xml (barcodes)|
| `/ws/2/recording/?client=<C>`         | POST       | application/xml (ISRCs)   |
| `/ws/2/collection/<id>/<type>/<ids>`  | PUT/DELETE  | (no body)                 |

## Authentication

- Digest auth: `httpx.DigestAuth(username, password)` over HTTPS
- OAuth2: for user-scoped data (user-tags, user-ratings, user-genres, collections)

## Release Type & Status Filters

- **status**: official, promotion, bootleg, pseudo-release, withdrawn, cancelled
- **type** (primary): album, single, ep, broadcast, other
- **type** (secondary): compilation, soundtrack, live, remix, demo, audiobook, etc.

## Annotations

Entities may include an `annotation` field (when requested via `inc=annotation`).
Annotations use MusicBrainz wiki markup. The `annotation` module provides converters:

- `annotation_to_text(markup)` — strip all formatting to plain text
- `annotation_to_markdown(markup)` — convert to Markdown

See https://musicbrainz.org/doc/Annotation#Wiki_formatting for the markup spec.

## Forward Compatibility

All Pydantic models use `extra="allow"`, which means unknown fields returned by the API are preserved rather than discarded or rejected. If MusicBrainz adds a new field, your code won't break — the new field is stored in `model_extra`:

```python
artist = client.lookup_typed("artist", mbid)

# Declared fields work as usual with IDE autocompletion
artist.name     # "Metallica"
artist.country  # "US"

# New/unknown fields are preserved in model_extra
artist.model_extra  # {"some-new-field": "value"}
```

Once a typed attribute is added to the model in a library update, the field moves from `model_extra` to a proper attribute — no behavior change for existing code.

## Cover Art Archive

Separate API at `https://coverartarchive.org/`. No authentication or rate limiting required.

| Endpoint | Returns |
|---|---|
| `GET /release/<mbid>/` | JSON image listing |
| `GET /release-group/<mbid>/` | JSON image listing |
| `GET /release/<mbid>/front` | Front cover image (binary), 307 redirect to archive.org |
| `GET /release/<mbid>/back` | Back cover image (binary) |
| `GET /release/<mbid>/<image_id>` | Specific image (binary) |

Thumbnail sizes: append `-250`, `-500`, or `-1200` to the image path (e.g. `/release/<mbid>/front-500`).

Use `HEAD` requests to get `Content-Type` and `Content-Length` without downloading the image.

## Environment Variables

Client defaults can be set via environment variables. Explicit constructor arguments always take precedence.

| Variable | Overrides |
|---|---|
| `MUSICBRAINZPY_APP` | `app_name` |
| `MUSICBRAINZPY_VERSION` | `app_version` |
| `MUSICBRAINZPY_CONTACT` | `app_contact` |
| `MUSICBRAINZPY_BASE_URL` | `base_url` |
| `MUSICBRAINZPY_USERNAME` | `username` |
| `MUSICBRAINZPY_PASSWORD` | `password` |
