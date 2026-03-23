from __future__ import annotations

from musicbrainzpy.annotation import annotation_to_markdown, annotation_to_text

SAMPLE = (
    "= Title =\r\n"
    "== Subtitle ==\r\n"
    "'''''bold italic''''' '''bold''' ''italic''\r\n"
    "----\r\n"
    "    * bullet\r\n"
    "        code line\r\n"
    "[http://example.com|Link] and [http://bare.url]\r\n"
    "&#91;escaped&#93;"
)


class TestAnnotationToText:
    def test_headings(self) -> None:
        assert annotation_to_text("= Title =") == "Title"

    def test_bold_italic_stripped(self) -> None:
        assert annotation_to_text("'''bold''' ''italic'' '''''both'''''") == "bold italic both"

    def test_links_resolved(self) -> None:
        assert annotation_to_text("[http://x.com|Label]") == "Label"
        assert annotation_to_text("[http://x.com]") == "http://x.com"

    def test_hr_removed(self) -> None:
        assert "----" not in annotation_to_text("before\r\n----\r\nafter")

    def test_bullets(self) -> None:
        assert "  •" in annotation_to_text("    * item")

    def test_code(self) -> None:
        assert annotation_to_text("        code") == "code"

    def test_html_entities(self) -> None:
        assert annotation_to_text("&#91;x&#93;") == "[x]"

    def test_full_sample(self) -> None:
        text = annotation_to_text(SAMPLE)
        assert "Title" in text
        assert "'''" not in text
        assert "----" not in text
        assert "[escaped]" in text


class TestAnnotationToMarkdown:
    def test_headings(self) -> None:
        assert annotation_to_markdown("= H1 =") == "# H1"
        assert annotation_to_markdown("== H2 ==") == "## H2"
        assert annotation_to_markdown("=== H3 ===") == "### H3"

    def test_bold_italic(self) -> None:
        assert annotation_to_markdown("'''b'''") == "**b**"
        assert annotation_to_markdown("''i''") == "*i*"
        assert annotation_to_markdown("'''''bi'''''") == "***bi***"

    def test_links(self) -> None:
        assert annotation_to_markdown("[http://x.com|Label]") == "[Label](http://x.com)"
        assert annotation_to_markdown("[http://x.com]") == "http://x.com"

    def test_hr(self) -> None:
        assert "---" in annotation_to_markdown("----")

    def test_bullets(self) -> None:
        assert annotation_to_markdown("    * item") == "- item"

    def test_code(self) -> None:
        assert annotation_to_markdown("        code") == "    code"

    def test_html_entities(self) -> None:
        assert annotation_to_markdown("&#91;x&#93;") == "[x]"

    def test_full_sample(self) -> None:
        md = annotation_to_markdown(SAMPLE)
        assert "# Title" in md
        assert "**bold**" in md
        assert "---" in md
        assert "[Link](http://example.com)" in md
