# Migrating from musicbrainzngs

This guide helps you move from [python-musicbrainzngs](https://github.com/alastair/python-musicbrainzngs) to musicbrainzpy.

## Key differences

| | musicbrainzngs | musicbrainzpy |
|---|---|---|
| API format | XML (parsed to dicts) | JSON (native) |
| Architecture | Module-level global state | Instance-based clients |
| Async support | No | Yes (+ sync client) |
| Return types | Plain dicts | Pydantic models or dicts |
| Python | 2.7+ / 3.x | 3.12+ |
| HTTP library | urllib | httpx |
| Auth | Digest only | Digest + OAuth2 |

## Response format

This is the most important difference. musicbrainzngs parses XML responses into dicts with a specific structure (`-list` suffixes, string values for counts, etc.). musicbrainzpy uses the JSON API, which returns a different dict structure.

If your code accesses specific dict keys from musicbrainzngs responses, you'll need to update those. The typed API (`lookup_typed`, `search_typed`, `browse_typed`) avoids this problem entirely by giving you Pydantic models with documented attributes.

```python
# musicbrainzngs — XML-parsed dict
result = musicbrainzngs.get_artist_by_id(mbid, includes=["tags"])
tags = result["artist"]["tag-list"]  # list of {"name": ..., "count": "5"}

# musicbrainzpy — typed model
artist = client.lookup_typed("artist", mbid, includes=["tags"])
tags = artist.tags  # list of Tag(name=..., count=5)

# musicbrainzpy — raw dict (JSON API format)
data = client.lookup("artist", mbid, includes=["tags"])
tags = data["tags"]  # list of {"name": ..., "count": 5}
```

## Setup

```python
# --- musicbrainzngs ---
import musicbrainzngs
musicbrainzngs.set_useragent("myapp", "1.0", "me@example.com")

# --- musicbrainzpy (sync) ---
from musicbrainzpy import SyncMusicBrainzClient
client = SyncMusicBrainzClient("myapp", "1.0", "me@example.com")

# --- musicbrainzpy (async) ---
from musicbrainzpy import MusicBrainzClient
client = MusicBrainzClient("myapp", "1.0", "me@example.com")
```

Use as a context manager to ensure cleanup:

```python
with SyncMusicBrainzClient("myapp", "1.0", "me@example.com") as client:
    ...

async with MusicBrainzClient("myapp", "1.0", "me@example.com") as client:
    ...
```

### Custom hostname

```python
# musicbrainzngs
musicbrainzngs.set_hostname("my-mirror.example.com", use_https=True)

# musicbrainzpy
client = SyncMusicBrainzClient("myapp", "1.0", "me@example.com",
                                base_url="https://my-mirror.example.com/ws/2/")
```

### Rate limiting

```python
# musicbrainzngs
musicbrainzngs.set_rate_limit(limit_or_interval=2.0)

# musicbrainzpy
client = SyncMusicBrainzClient("myapp", "1.0", "me@example.com", rate_limit=2.0)
```

### Authentication

```python
# musicbrainzngs
musicbrainzngs.auth("user", "pass")

# musicbrainzpy — digest auth (async client only for submissions)
client = MusicBrainzClient("myapp", "1.0", "me@example.com",
                           username="user", password="pass")

# musicbrainzpy — OAuth2 (recommended)
from musicbrainzpy import OAuthHandler
oauth = OAuthHandler("client-id", "client-secret", "http://localhost:8080/callback")
await oauth.exchange_code("authorization-code")
client = MusicBrainzClient("myapp", "1.0", "me@example.com", oauth=oauth)
```

## Lookups

musicbrainzngs has a separate function per entity type. musicbrainzpy uses a single method with the entity type as a parameter.

```python
# musicbrainzngs
result = musicbrainzngs.get_artist_by_id(mbid, includes=["releases", "tags"])
artist_dict = result["artist"]

result = musicbrainzngs.get_release_by_id(mbid, includes=["recordings"])
release_dict = result["release"]

result = musicbrainzngs.get_release_group_by_id(mbid)
rg_dict = result["release-group"]

# musicbrainzpy — typed (recommended)
artist = client.lookup_typed("artist", mbid, includes=["releases", "tags"])
release = client.lookup_typed("release", mbid, includes=["recordings"])
rg = client.lookup_typed("release-group", mbid)

# musicbrainzpy — raw dict
data = client.lookup("artist", mbid, includes=["releases", "tags"])
data = client.lookup("release", mbid, includes=["recordings"])
data = client.lookup("release-group", mbid)
```

All entity types: `artist`, `release`, `release-group`, `recording`, `work`, `label`, `area`, `event`, `instrument`, `place`, `series`, `url`.

## Searching

```python
# musicbrainzngs
result = musicbrainzngs.search_artists(artist="Metallica", limit=10)
artists = result["artist-list"]

result = musicbrainzngs.search_releases(artist="Björk", release="Homogenic", strict=True)
releases = result["release-list"]

# musicbrainzpy — typed
result = client.search_typed("artist", "Metallica", limit=10)
artists = result.items  # list of Artist models
total = result.count

# musicbrainzpy — raw dict
data = client.search("artist", "Metallica", limit=10)
artists = data["artists"]
```

### Search fields

musicbrainzngs accepts search fields as keyword arguments and builds a Lucene query. In musicbrainzpy, you write the Lucene query directly:

```python
# musicbrainzngs
musicbrainzngs.search_releases(artist="Björk", release="Homogenic", strict=True)

# musicbrainzpy — equivalent Lucene query
client.search("release", 'artist:"Björk" AND release:"Homogenic"')

# musicbrainzngs (non-strict, fuzzy)
musicbrainzngs.search_artists(artist="Metallica", country="US")

# musicbrainzpy
client.search("artist", "artist:Metallica country:US")
```

## Browsing

musicbrainzngs has separate functions per entity type with keyword arguments for the linked entity. musicbrainzpy uses a single method.

```python
# musicbrainzngs
result = musicbrainzngs.browse_releases(artist=artist_mbid, limit=100, offset=0,
                                         includes=["labels"])
releases = result["release-list"]
total = result["release-count"]

result = musicbrainzngs.browse_release_groups(artist=artist_mbid, release_type=["album"])

# musicbrainzpy — typed
result = client.browse_typed("release", linked_type="artist", linked_id=artist_mbid,
                              limit=100, offset=0, includes=["labels"])
releases = result.items  # list of Release models
total = result.count

# musicbrainzpy — raw dict
data = client.browse("release", linked_type="artist", linked_id=artist_mbid,
                      limit=100, offset=0, includes=["labels"])
```

> **Note:** musicbrainzngs `release_type` and `release_status` filters are passed as `type` and `status` includes in musicbrainzpy — these are query parameters on the browse endpoint.

## Non-MBID lookups

```python
# musicbrainzngs
result = musicbrainzngs.get_recordings_by_isrc("USEE10100063")
recordings = result["isrc"]["recording-list"]

result = musicbrainzngs.get_works_by_iswc("T-070.116.274-5")
works = result["work-list"]

result = musicbrainzngs.get_releases_by_discid(discid, toc="1+12+267257+150")

# musicbrainzpy
recordings = client.lookup_by_isrc("USEE10100063")       # list[Recording]
works = client.lookup_by_iswc("T-070.116.274-5")         # list[Work]
releases = client.lookup_by_discid(discid, toc="1+12+267257+150")  # list[Release]
```

## Submissions

Submissions require the async `MusicBrainzClient` with authentication.

```python
# musicbrainzngs
musicbrainzngs.submit_tags(artist_tags={mbid: ["rock", "metal"]})
musicbrainzngs.submit_ratings(artist_ratings={mbid: 80})
musicbrainzngs.submit_barcodes({release_mbid: "4050538793819"})
musicbrainzngs.submit_isrcs({recording_mbid: ["USEE10100063"]})

# musicbrainzpy (async)
await client.submit_tags("myapp-1.0", {"artist": {mbid: ["rock", "metal"]}})
await client.submit_ratings("myapp-1.0", {"artist": {mbid: 80}})
await client.submit_barcodes("myapp-1.0", {release_mbid: "4050538793819"})
await client.submit_isrcs("myapp-1.0", {recording_mbid: ["USEE10100063"]})
```

Key differences:
- musicbrainzpy requires a `client_id` string (e.g. `"myapp-1.0"`) as the first argument
- Tags/ratings are nested under entity type: `{"artist": {mbid: ...}}` instead of `artist_tags={mbid: ...}`

## Collections

```python
# musicbrainzngs
musicbrainzngs.add_releases_to_collection(collection_mbid, [release_mbid])
musicbrainzngs.remove_releases_from_collection(collection_mbid, [release_mbid])

# musicbrainzpy (async) — supports any entity type, not just releases
await client.collection_add("myapp-1.0", collection_mbid, "releases", [release_mbid])
await client.collection_remove("myapp-1.0", collection_mbid, "releases", [release_mbid])
```

## Exceptions

| musicbrainzngs | musicbrainzpy |
|---|---|
| `MusicBrainzError` | `MusicBrainzError` |
| `WebServiceError` | `MusicBrainzError` (base class) |
| `AuthenticationError` | `AuthenticationError` |
| `NetworkError` | `httpx.TransportError` (from httpx) |
| `ResponseError` | `InvalidRequestError`, `NotFoundError`, `RateLimitedError` |
| `UsageError` | `ValueError` (standard Python) |

```python
# musicbrainzngs
from musicbrainzngs import WebServiceError, ResponseError
try:
    musicbrainzngs.get_artist_by_id(mbid)
except ResponseError as e:
    print(e)

# musicbrainzpy
from musicbrainzpy import NotFoundError, MusicBrainzError
try:
    client.lookup_typed("artist", mbid)
except NotFoundError:
    print("Not found")
except MusicBrainzError as e:
    print(e)
```

## Features not yet in musicbrainzpy

- **Cover Art Archive** — `get_image`, `get_image_front`, `get_image_back`, `get_image_list`, `get_release_group_image_list`, `get_release_group_image_front`
- **`get_collections`** / **`get_releases_in_collection`** — browsing collection contents
- **`search_annotations`** — annotation search
- **Custom response parsers** — `set_parser()`, `set_format()`

## Quick reference

| musicbrainzngs | musicbrainzpy |
|---|---|
| `set_useragent(app, ver, contact)` | `SyncMusicBrainzClient(app, ver, contact)` |
| `set_hostname(host, use_https)` | `base_url=` constructor arg |
| `set_rate_limit(interval)` | `rate_limit=` constructor arg |
| `auth(user, pass)` | `username=`/`password=` or `oauth=` constructor arg |
| `get_artist_by_id(id, includes)` | `client.lookup_typed("artist", id, includes)` |
| `get_release_by_id(id, includes)` | `client.lookup_typed("release", id, includes)` |
| `get_release_group_by_id(id, includes)` | `client.lookup_typed("release-group", id, includes)` |
| `get_recording_by_id(id, includes)` | `client.lookup_typed("recording", id, includes)` |
| `get_label_by_id(id, includes)` | `client.lookup_typed("label", id, includes)` |
| `get_work_by_id(id, includes)` | `client.lookup_typed("work", id, includes)` |
| `get_area_by_id(id, includes)` | `client.lookup_typed("area", id, includes)` |
| `get_event_by_id(id, includes)` | `client.lookup_typed("event", id, includes)` |
| `get_instrument_by_id(id, includes)` | `client.lookup_typed("instrument", id, includes)` |
| `get_place_by_id(id, includes)` | `client.lookup_typed("place", id, includes)` |
| `get_series_by_id(id, includes)` | `client.lookup_typed("series", id, includes)` |
| `get_url_by_id(id, includes)` | `client.lookup_typed("url", id, includes)` |
| `get_recordings_by_isrc(isrc)` | `client.lookup_by_isrc(isrc)` |
| `get_works_by_iswc(iswc)` | `client.lookup_by_iswc(iswc)` |
| `get_releases_by_discid(id, toc=)` | `client.lookup_by_discid(id, toc=)` |
| `search_artists(query, **fields)` | `client.search_typed("artist", query)` |
| `search_releases(query, **fields)` | `client.search_typed("release", query)` |
| `search_recordings(query, **fields)` | `client.search_typed("recording", query)` |
| `search_release_groups(query, **fields)` | `client.search_typed("release-group", query)` |
| `search_labels(query, **fields)` | `client.search_typed("label", query)` |
| `search_works(query, **fields)` | `client.search_typed("work", query)` |
| `search_areas(query, **fields)` | `client.search_typed("area", query)` |
| `search_events(query, **fields)` | `client.search_typed("event", query)` |
| `search_instruments(query, **fields)` | `client.search_typed("instrument", query)` |
| `search_places(query, **fields)` | `client.search_typed("place", query)` |
| `search_series(query, **fields)` | `client.search_typed("series", query)` |
| `browse_releases(artist=id)` | `client.browse_typed("release", linked_type="artist", linked_id=id)` |
| `browse_release_groups(artist=id)` | `client.browse_typed("release-group", linked_type="artist", linked_id=id)` |
| `browse_recordings(artist=id)` | `client.browse_typed("recording", linked_type="artist", linked_id=id)` |
| `browse_artists(release=id)` | `client.browse_typed("artist", linked_type="release", linked_id=id)` |
| `browse_labels(release=id)` | `client.browse_typed("label", linked_type="release", linked_id=id)` |
| `browse_events(artist=id)` | `client.browse_typed("event", linked_type="artist", linked_id=id)` |
| `browse_places(area=id)` | `client.browse_typed("place", linked_type="area", linked_id=id)` |
| `submit_tags(artist_tags={})` | `await client.submit_tags(client_id, {"artist": {}})` |
| `submit_ratings(artist_ratings={})` | `await client.submit_ratings(client_id, {"artist": {}})` |
| `submit_barcodes({id: barcode})` | `await client.submit_barcodes(client_id, {id: barcode})` |
| `submit_isrcs({id: [isrc]})` | `await client.submit_isrcs(client_id, {id: [isrc]})` |
| `add_releases_to_collection(coll, ids)` | `await client.collection_add(client_id, coll, "releases", ids)` |
| `remove_releases_from_collection(coll, ids)` | `await client.collection_remove(client_id, coll, "releases", ids)` |
