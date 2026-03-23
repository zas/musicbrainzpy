"""XML body builders for MusicBrainz API submissions.

The MusicBrainz API only accepts XML for data submissions.
These helpers build the minimal XML documents needed.
"""

from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, tostring

_NS = "http://musicbrainz.org/ns/mmd-2.0#"


def _root() -> Element:
    """Create a root ``<metadata>`` element with the MusicBrainz namespace."""
    return Element("metadata", xmlns=_NS)


def build_tag_xml(entities: dict[str, dict[str, list[str]]]) -> str:
    """Build XML for tag submission.

    Args:
        entities: Mapping of entity type → {mbid: [tag_names]}.
            Example: ``{"artist": {"<mbid>": ["rock", "metal"]}}``

    Returns:
        XML string ready for POST to ``/ws/2/tag``.
    """
    root = _root()
    for entity_type, items in entities.items():
        list_el = SubElement(root, f"{entity_type}-list")
        for mbid, tags in items.items():
            entity_el = SubElement(list_el, entity_type, id=mbid)
            tag_list_el = SubElement(entity_el, "user-tag-list")
            for tag in tags:
                tag_el = SubElement(tag_list_el, "user-tag")
                name_el = SubElement(tag_el, "name")
                name_el.text = tag
    return tostring(root, encoding="unicode", xml_declaration=True)


def build_rating_xml(entities: dict[str, dict[str, int]]) -> str:
    """Build XML for rating submission.

    Args:
        entities: Mapping of entity type → {mbid: rating_value (0-100)}.
            Example: ``{"artist": {"<mbid>": 80}}``

    Returns:
        XML string ready for POST to ``/ws/2/rating``.
    """
    root = _root()
    for entity_type, items in entities.items():
        list_el = SubElement(root, f"{entity_type}-list")
        for mbid, rating in items.items():
            entity_el = SubElement(list_el, entity_type, id=mbid)
            rating_el = SubElement(entity_el, "user-rating")
            rating_el.text = str(rating)
    return tostring(root, encoding="unicode", xml_declaration=True)


def build_barcode_xml(barcodes: dict[str, str]) -> str:
    """Build XML for barcode submission.

    Args:
        barcodes: Mapping of release MBID → barcode (EAN/UPC).

    Returns:
        XML string ready for POST to ``/ws/2/release/``.
    """
    root = _root()
    list_el = SubElement(root, "release-list")
    for mbid, barcode in barcodes.items():
        release_el = SubElement(list_el, "release", id=mbid)
        barcode_el = SubElement(release_el, "barcode")
        barcode_el.text = barcode
    return tostring(root, encoding="unicode", xml_declaration=True)


def build_isrc_xml(isrcs: dict[str, list[str]]) -> str:
    """Build XML for ISRC submission.

    Args:
        isrcs: Mapping of recording MBID → list of ISRCs.

    Returns:
        XML string ready for POST to ``/ws/2/recording/``.
    """
    root = _root()
    list_el = SubElement(root, "recording-list")
    for mbid, isrc_list in isrcs.items():
        recording_el = SubElement(list_el, "recording", id=mbid)
        isrc_list_el = SubElement(recording_el, "isrc-list", count=str(len(isrc_list)))
        for isrc in isrc_list:
            SubElement(isrc_list_el, "isrc", id=isrc)
    return tostring(root, encoding="unicode", xml_declaration=True)
