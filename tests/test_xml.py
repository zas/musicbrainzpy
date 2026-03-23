"""Tests for XML body builders."""

from __future__ import annotations

from xml.etree.ElementTree import fromstring

from musicbrainzpy._xml import build_barcode_xml, build_isrc_xml, build_rating_xml, build_tag_xml

_NS = "http://musicbrainz.org/ns/mmd-2.0#"


def _find(root, path: str):  # noqa: ANN001, ANN202
    """Find element using namespace-qualified path."""
    return root.find(path.replace("/", f"/{{{_NS}}}" if "/" in path else "").replace("//", f"//{{{_NS}}}"))


class TestBuildTagXml:
    def test_single_entity(self) -> None:
        xml = build_tag_xml({"artist": {"abc-123": ["rock", "metal"]}})
        root = fromstring(xml)
        tags = root.findall(f".//{{{_NS}}}name")
        assert [t.text for t in tags] == ["rock", "metal"]

    def test_multiple_entity_types(self) -> None:
        xml = build_tag_xml(
            {
                "artist": {"abc": ["rock"]},
                "recording": {"def": ["noise"]},
            }
        )
        root = fromstring(xml)
        assert root.find(f"{{{_NS}}}artist-list") is not None
        assert root.find(f"{{{_NS}}}recording-list") is not None


class TestBuildRatingXml:
    def test_single_rating(self) -> None:
        xml = build_rating_xml({"artist": {"abc-123": 80}})
        root = fromstring(xml)
        rating = root.find(f".//{{{_NS}}}user-rating")
        assert rating is not None
        assert rating.text == "80"


class TestBuildBarcodeXml:
    def test_single_barcode(self) -> None:
        xml = build_barcode_xml({"abc-123": "4050538793819"})
        root = fromstring(xml)
        barcode = root.find(f".//{{{_NS}}}barcode")
        assert barcode is not None
        assert barcode.text == "4050538793819"
        release = root.find(f".//{{{_NS}}}release")
        assert release is not None
        assert release.get("id") == "abc-123"


class TestBuildIsrcXml:
    def test_single_recording(self) -> None:
        xml = build_isrc_xml({"abc-123": ["USEE10100063", "GBAYE0000001"]})
        root = fromstring(xml)
        isrcs = root.findall(f".//{{{_NS}}}isrc")
        assert len(isrcs) == 2
        assert isrcs[0].get("id") == "USEE10100063"
        assert isrcs[1].get("id") == "GBAYE0000001"
        isrc_list = root.find(f".//{{{_NS}}}isrc-list")
        assert isrc_list is not None
        assert isrc_list.get("count") == "2"
