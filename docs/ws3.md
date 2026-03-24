# Web Service v3 (ws/3) Preparation

MusicBrainz is planning a ws/3 revision of their API. There is no timeline or beta endpoint yet — these are open tickets on the [MetaBrainz tracker](https://tickets.metabrainz.org/issues/?jql=project+%3D+MBS+AND+fixVersion+%3D+%22ws%2F3%22).

## What musicbrainzpy does today

- **`api_version` parameter** — Both clients accept `api_version="3"` (default `"2"`). This builds the base URL as `https://musicbrainz.org/ws/{api_version}/`. Ignored when `base_url` is set explicitly.
- **`extra="allow"` on all models** — New fields returned by ws/3 will be captured automatically without breaking existing code.
- **Unprefixed browse count/offset** — `BrowseResult` parsing accepts both `"count"` / `"offset"` (ws/3) and `"recording-count"` / `"recording-offset"` (ws/2). See [MBS-9731](https://tickets.metabrainz.org/browse/MBS-9731).

## Known ws/3 changes

### Structural (will need model changes)

**[MBS-9829](https://tickets.metabrainz.org/browse/MBS-9829) — Nested objects instead of flat id/name pairs**

Currently: `"packaging-id": "119eba76-...", "packaging": "None"` (two flat fields).
Planned: `"packaging": {"id": "119eba76-...", "name": "None"}` (single nested object).

Affects many fields across Release, Recording, and other entities. Will require new or updated Pydantic models — a single model cannot cleanly handle both shapes.

**[MBS-5679](https://tickets.metabrainz.org/browse/MBS-5679) — Consistent `name` vs `title`**

Currently releases and release groups use `title`, other entities use `name`. ws/3 may unify this. Direction not yet decided.

### Cleanup (minor or already handled)

**[MBS-11343](https://tickets.metabrainz.org/browse/MBS-11343) — Drop area/label `sort-name`**

These are just copies of `name` (removed from the database years ago). Our models already have `sort_name` as `Optional`, so removal won't break anything.

**[MBS-11266](https://tickets.metabrainz.org/browse/MBS-11266) — Unify rating scale**

`/ws/2/rating` returns 0–100, but `inc=user-ratings` on entity lookups returns 0–5. ws/3 will pick one scale.

**[MBS-9731](https://tickets.metabrainz.org/browse/MBS-9731) — Unprefixed count/offset in browse** ✅

Already handled — see above.

### Current ws/2 quirks (no fix version, may be addressed in ws/3)

**[MBS-13520](https://tickets.metabrainz.org/browse/MBS-13520) — Empty lists omitted instead of `[]`**

Loaded but empty arrays (e.g. `release-events`, `tracks`) are omitted entirely. Already handled by our `list[X] | None = None` defaults.

**[MBS-13519](https://tickets.metabrainz.org/browse/MBS-13519) — Inconsistent date serialization**

Dates may be omitted, `""`, or `null` depending on the field and entity. Already handled by `str | None = None`.

## When ws/3 ships

The `api_version` parameter lets users opt in immediately. For full support, we'll likely need:

1. Updated models for nested objects (MBS-9829) — either version-aware validators or a separate model set
2. Updated field names if `title` → `name` unification happens (MBS-5679)
3. Rating scale normalization (MBS-11266)
