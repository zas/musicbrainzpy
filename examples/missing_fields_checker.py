#!/usr/bin/env python3
"""Check all entity models against the live MusicBrainz API for unmapped fields.

Usage:
    uv run python examples/missing_fields_checker.py

Queries every entity type with maximal inc= parameters and runs searches,
then reports any JSON fields not declared in the Pydantic models.
"""

from __future__ import annotations

import logging
import sys
from collections import defaultdict

logging.basicConfig(stream=sys.stdout, level=logging.WARNING, format="%(message)s")

# Capture unmapped field warnings
unmapped: dict[str, set[str]] = defaultdict(set)
_original_debug = logging.Logger.debug


def _capture_debug(self: logging.Logger, msg: object, *args: object, **kwargs: object) -> None:
    text = str(msg) % args if args else str(msg)
    if text.startswith("Unmapped fields on "):
        rest = text[len("Unmapped fields on ") :]
        model, _, fields_str = rest.partition(": ")
        for f in eval(fields_str):  # noqa: S307
            unmapped[model].add(f)
        return  # suppress output — we report these at the end
    _original_debug(self, msg, *args)


logging.Logger.debug = _capture_debug  # type: ignore[assignment]
logging.getLogger("musicbrainzpy").setLevel(logging.DEBUG)

from musicbrainzpy import SyncMusicBrainzClient  # noqa: E402
from musicbrainzpy.exceptions import MusicBrainzError  # noqa: E402

METALLICA = "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"
ENTER_SANDMAN_REC = "ba5d0553-032f-4127-aed7-4d2e0d18f3f9"
ENTER_SANDMAN_WORK = "e5f97e53-ed4d-3721-afb5-5c47dda08782"
BLACK_ALBUM_RG = "dd4b2235-a53c-4da5-b2f9-6d438b3a6229"
RELEASE_CD = "cffc9bff-6253-4c5c-a0d8-55878b5edf1f"
ELEKTRA = "873f9f75-af68-4872-98e2-431058e4c9a9"
USA = "489ce91b-6658-3307-9877-795b68554c98"
GUITAR = "63021302-86cd-4aee-80df-2270d54f4978"
PLACE = "4352063b-a833-421b-a420-e7fb295dece0"
EVENT = "e76ab257-286b-45db-b9e6-5a51b3ecbe23"
SERIES = "07069d80-622a-4ad1-ba57-25d88ce3210d"
GENRE = "911c7bbb-172d-4df8-9478-dbff4296e791"

ALL_INC = ["tags", "genres", "ratings", "aliases", "annotation"]
errors: list[str] = []


def run(label: str, func: object, *args: object, **kwargs: object) -> None:
    """Run a check, catching errors so the script continues."""
    try:
        func(*args, **kwargs)  # type: ignore[operator]
    except (MusicBrainzError, Exception) as exc:
        errors.append(f"{label}: {exc}")
        print(f"  ERROR: {label}: {exc}", file=sys.stderr)


with SyncMusicBrainzClient("musicbrainzpy-fieldcheck", "0.1", "test@example.com", rate_limit=1.1) as c:
    print("Checking lookups...", flush=True)
    run(
        "artist",
        c.lookup_typed,
        "artist",
        METALLICA,
        includes=[*ALL_INC, "release-groups", "releases", "works", "recordings"],
    )
    run(
        "release",
        c.lookup_typed,
        "release",
        RELEASE_CD,
        includes=[
            "recordings",
            "labels",
            "artist-credits",
            "media",
            "release-groups",
            "tags",
            "genres",
            "aliases",
            "annotation",
            "discids",
            "isrcs",
        ],
    )
    run(
        "recording",
        c.lookup_typed,
        "recording",
        ENTER_SANDMAN_REC,
        includes=[*ALL_INC, "artist-credits", "isrcs", "releases"],
    )
    run(
        "release-group",
        c.lookup_typed,
        "release-group",
        BLACK_ALBUM_RG,
        includes=[*ALL_INC, "artist-credits", "releases"],
    )
    run("label", c.lookup_typed, "label", ELEKTRA, includes=[*ALL_INC, "releases"])
    run("work", c.lookup_typed, "work", ENTER_SANDMAN_WORK, includes=ALL_INC)
    run("area", c.lookup_typed, "area", USA, includes=["tags", "genres", "aliases", "annotation"])
    run("event", c.lookup_typed, "event", EVENT, includes=ALL_INC)
    run("place", c.lookup_typed, "place", PLACE, includes=["tags", "genres", "aliases", "annotation"])
    run("instrument", c.lookup_typed, "instrument", GUITAR, includes=["tags", "genres", "aliases", "annotation"])
    run("series", c.lookup_typed, "series", SERIES, includes=["tags", "genres", "aliases", "annotation"])
    run("genre", c.lookup_typed, "genre", GENRE)

    print("Checking searches...", flush=True)
    for entity in [
        "artist",
        "release",
        "recording",
        "release-group",
        "label",
        "work",
        "area",
        "event",
        "place",
        "instrument",
        "series",
        "annotation",
    ]:
        query = "Beethoven" if entity == "annotation" else "Metallica"
        run(f"search-{entity}", c.search_typed, entity, query, limit=2)

    print("Checking browses...", flush=True)
    for entity in ["release", "release-group", "recording", "work"]:
        run(f"browse-{entity}", c.browse_typed, entity, linked_type="artist", linked_id=METALLICA, limit=2)

# Filter out MBModel (generic fallback for circular import avoidance)
unmapped.pop("MBModel", None)

if unmapped:
    print(f"\n{'Model':<25} {'Unmapped fields'}")
    print("-" * 70)
    for model in sorted(unmapped):
        fields = ", ".join(sorted(unmapped[model]))
        print(f"{model:<25} {fields}")

if errors:
    print(f"\n{len(errors)} error(s) during checks:")
    for e in errors:
        print(f"  {e}")

if unmapped or errors:
    sys.exit(1)
else:
    print("\nAll fields mapped!")
