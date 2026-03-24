"""Display all information shown on a MusicBrainz recording page.

Replicates the content of:
    https://musicbrainz.org/recording/a35b5c60-fa36-4333-ae57-66519157c6fe

Usage:
    uv run python examples/recording_page.py [MBID]
"""

from __future__ import annotations

import sys
from collections import defaultdict

from musicbrainzpy import SyncMusicBrainzClient

RECORDING_MBID = "a35b5c60-fa36-4333-ae57-66519157c6fe"


def fmt_duration(ms: int | None) -> str:
    if ms is None:
        return "?:??"
    return f"{ms // 60000}:{(ms % 60000) // 1000:02d}"


def print_section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def main(mbid: str) -> None:
    with SyncMusicBrainzClient("musicbrainzpy-examples", "0.1.0", "you@example.com") as c:
        # --- Recording lookup with all relevant includes ---
        rec = c.lookup(
            "recording",
            mbid,
            includes=[
                "artist-credits",
                "isrcs",
                "tags",
                "genres",
                "ratings",
                "artist-rels",
                "place-rels",
                "url-rels",
                "work-rels",
                "work-level-rels",
            ],
        )

        # --- Header ---
        artist_credit = " / ".join(ac.get("name", ac["artist"]["name"]) for ac in rec.get("artist-credit", []))
        disambig = f" ({rec['disambiguation']})" if rec.get("disambiguation") else ""
        print(f"\n  {rec['title']}{disambig}")
        print(f"  Recording by {artist_credit}")

        # --- Recording information ---
        print_section("Recording information")
        print(f"  Artist:             {artist_credit}")
        print(f"  Length:             {fmt_duration(rec.get('length'))}")
        print(f"  First release:      {rec.get('first-release-date', '?')}")
        for isrc in rec.get("isrcs", []):
            print(f"  ISRC:               {isrc}")

        # --- Rating ---
        rating = rec.get("rating", {})
        if rating.get("value") is not None:
            print(f"\n  Rating:             {rating['value']} ({rating.get('votes-count', 0)} votes)")

        # --- Tags & Genres ---
        genres = rec.get("genres", [])
        tags = rec.get("tags", [])
        genre_names = {g["name"] for g in genres}
        other_tags = [t for t in tags if t["name"] not in genre_names]

        if genres:
            print_section("Genres")
            for g in sorted(genres, key=lambda x: -x.get("count", 0)):
                print(f"  {g['name']} ({g['count']})")

        if other_tags:
            print_section("Other tags")
            for t in sorted(other_tags, key=lambda x: -x.get("count", 0)):
                print(f"  {t['name']} ({t['count']})")

        # --- Relationships ---
        rels = rec.get("relations", [])

        # Group by target type
        artist_rels: dict[str, list[str]] = defaultdict(list)
        places: dict[str, list[str]] = defaultdict(list)
        urls: dict[str, list[str]] = defaultdict(list)
        work_id = None
        work_title = None

        for r in rels:
            target = r.get("target-type", "")
            rel_type = r.get("type", "")
            attrs = r.get("attributes", [])
            begin = r.get("begin", "")
            end = r.get("end", "")
            period = f" ({begin} – {end})" if begin or end else ""

            if target == "artist":
                name = r["artist"]["name"]
                disambig_a = f" ({r['artist']['disambiguation']})" if r["artist"].get("disambiguation") else ""
                # Combine instrument/vocal attributes with relationship type
                if rel_type == "instrument":
                    label = ", ".join(attrs) if attrs else "instrument"
                elif rel_type == "vocal":
                    label = ", ".join(attrs) if attrs else "vocals"
                elif rel_type == "engineer" and "assistant" in attrs:
                    label = "assistant engineer"
                elif rel_type == "performing orchestra":
                    label = "orchestra"
                else:
                    label = rel_type
                artist_rels[label].append(f"{name}{disambig_a}{period}")

            elif target == "place":
                name = r["place"]["name"]
                places[rel_type].append(f"{name}{period}")

            elif target == "url":
                url = r["url"]["resource"]
                urls[rel_type].append(url)

            elif target == "work":
                work_id = r["work"]["id"]
                work_title = r["work"]["title"]

        if artist_rels:
            print_section("Relationships — Artists")
            for label in sorted(artist_rels):
                for name in artist_rels[label]:
                    print(f"  {label + ':':<30} {name}")

        if places:
            print_section("Relationships — Places")
            for label in sorted(places):
                for name in places[label]:
                    print(f"  {label + ':':<30} {name}")

        if urls:
            print_section("External links")
            for label in sorted(urls):
                for url in urls[label]:
                    print(f"  {label + ':':<30} {url}")

        # --- Related work (composer, lyricist, publishers) ---
        if work_id:
            work = c.lookup("work", work_id, includes=["artist-rels", "label-rels"])
            print_section(f"Related work — {work_title}")

            work_rels = work.get("relations", [])
            for wr in work_rels:
                tt = wr.get("target-type", "")
                rt = wr.get("type", "")
                if tt == "artist":
                    name = wr["artist"]["name"]
                    print(f"  {rt + ':':<30} {name}")
                elif tt == "label":
                    name = wr["label"]["name"]
                    print(f"  {rt + ':':<30} {name}")

        # --- Appears on releases ---
        print_section("Appears on releases")
        offset = 0
        count = 0
        while True:
            page = c.browse(
                "release",
                linked_type="recording",
                linked_id=mbid,
                limit=100,
                offset=offset,
                includes=["labels", "artist-credits", "release-groups", "media"],
            )
            releases = page.get("releases", [])
            for rel in releases:
                title = rel["title"]
                status = rel.get("status", "")
                date = rel.get("date", "")
                country = rel.get("country", "")
                rg = rel.get("release-group", {})
                rg_type = rg.get("primary-type", "")
                secondary = rg.get("secondary-types", [])
                if secondary:
                    rg_type += " + " + ", ".join(secondary)

                labels_info = []
                for li in rel.get("label-info", []):
                    lbl = li.get("label", {})
                    lname = lbl.get("name", "") if lbl else ""
                    catno = li.get("catalog-number", "")
                    if lname or catno:
                        labels_info.append(f"{lname} ({catno})" if catno else lname)

                rel_artist = " / ".join(ac.get("name", ac["artist"]["name"]) for ac in rel.get("artist-credit", []))

                print(f"  [{status or '?':>10}] {title}")
                print(f"             Artist: {rel_artist}  Type: {rg_type}")
                print(f"             {country} {date}  Label: {', '.join(labels_info) or '—'}")

            total = page.get("release-count", 0)
            offset += len(releases)
            if not releases or offset >= total:
                count = total
                break

        print(f"\n  Total: {count} releases")


if __name__ == "__main__":
    mbid = sys.argv[1] if len(sys.argv) > 1 else RECORDING_MBID
    main(mbid)
