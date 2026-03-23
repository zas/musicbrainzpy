"""Convert MusicBrainz wiki-formatted annotations to plain text or Markdown.

MusicBrainz annotations use a custom wiki markup described at
https://musicbrainz.org/doc/Annotation#Wiki_formatting
"""

from __future__ import annotations

import re

# Bold+italic must come before bold and italic
_BOLD_ITALIC_RE = re.compile(r"'{5}(.+?)'{5}")
_BOLD_RE = re.compile(r"'{3}(.+?)'{3}")
_ITALIC_RE = re.compile(r"'{2}(.+?)'{2}")
_HEADING_RE = re.compile(r"^(={1,3})\s*(.+?)\s*\1\s*$", re.MULTILINE)
_LINK_RE = re.compile(r"\[([^\]|]+?)(?:\|([^\]]+?))?\]")
_HR_RE = re.compile(r"^----\s*$", re.MULTILINE)
_BULLET_RE = re.compile(r"^    \*", re.MULTILINE)
_CODE_RE = re.compile(r"^        ", re.MULTILINE)
_HTML_ENTITY_RE = re.compile(r"&#(\d+);")


def _decode_entities(text: str) -> str:
    return _HTML_ENTITY_RE.sub(lambda m: chr(int(m.group(1))), text)


def annotation_to_text(annotation: str) -> str:
    """Convert a MusicBrainz wiki annotation to plain text.

    Strips all formatting, resolves links to their display text or URL,
    and decodes HTML numeric entities.
    """
    text = annotation.replace("\r\n", "\n")
    text = _BOLD_ITALIC_RE.sub(r"\1", text)
    text = _BOLD_RE.sub(r"\1", text)
    text = _ITALIC_RE.sub(r"\1", text)
    text = _HEADING_RE.sub(r"\2", text)
    text = _LINK_RE.sub(lambda m: m.group(2) or m.group(1), text)
    text = _HR_RE.sub("", text)
    text = _BULLET_RE.sub("  •", text)
    text = _CODE_RE.sub("", text)
    return _decode_entities(text)


def annotation_to_markdown(annotation: str) -> str:
    """Convert a MusicBrainz wiki annotation to Markdown.

    Maps wiki headings to ``#``/``##``/``###``, bold/italic to ``**``/``*``,
    links to ``[text](url)``, bullets to ``-``, and code lines to backtick
    fences.
    """
    text = annotation.replace("\r\n", "\n")
    text = _BOLD_ITALIC_RE.sub(r"***\1***", text)
    text = _BOLD_RE.sub(r"**\1**", text)
    text = _ITALIC_RE.sub(r"*\1*", text)
    text = _HEADING_RE.sub(lambda m: "#" * len(m.group(1)) + " " + m.group(2), text)
    text = _LINK_RE.sub(lambda m: f"[{m.group(2) or m.group(1)}]({m.group(1)})" if m.group(2) else m.group(1), text)
    text = _HR_RE.sub("---", text)
    text = _BULLET_RE.sub("-", text)
    text = _CODE_RE.sub("    ", text)
    return _decode_entities(text)
