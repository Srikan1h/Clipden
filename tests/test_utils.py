"""
Unit tests for ClipDen utility functions.
"""

from clipden.utils import format_timestamp, generate_title, get_content_preview, validate_snippet


def test_generate_title_simple():
    title = generate_title("This is a simple test sentence")
    assert title == "This is a simple test sentence"


def test_generate_title_multiline():
    content = "First line of code\nSecond line of code\nThird line"
    title = generate_title(content)
    assert title.startswith("First line")
    assert title.endswith("…")


def test_generate_title_long_content():
    content = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"
    title = generate_title(content, max_words=5)
    assert title.endswith("…")
    assert "word5" in title
    assert "word6" not in title


def test_generate_title_empty():
    assert generate_title("") == "Untitled Snippet"
    assert generate_title("   \n\n  ") == "Untitled Snippet"


def test_validate_snippet():
    # Valid snippet
    valid, msg = validate_snippet("My Title", "My Content")
    assert valid is True
    assert msg == ""

    # Empty title
    valid, msg = validate_snippet("", "Some content")
    assert valid is False
    assert "Title" in msg

    # Whitespace title
    valid, msg = validate_snippet("   \t", "Some content")
    assert valid is False
    assert "Title" in msg

    # Empty content
    valid, msg = validate_snippet("Valid title", "")
    assert valid is False
    assert "Content" in msg

    # Whitespace content
    valid, msg = validate_snippet("Valid title", "   \n  ")
    assert valid is False
    assert "Content" in msg


def test_format_timestamp():
    # Valid ISO timestamp
    iso_ts = "2026-11-15T12:00:00+00:00"
    formatted = format_timestamp(iso_ts)
    assert len(formatted) > 0

    # Empty
    assert format_timestamp("") == ""


def test_get_content_preview():
    multiline = "Line 1\n   Line 2\n\nLine 3"
    preview = get_content_preview(multiline, max_chars=30)
    assert "\n" not in preview
    assert "Line 1 Line 2" in preview

