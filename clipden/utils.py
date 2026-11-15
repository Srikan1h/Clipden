"""
Utility functions for ClipDen.
"""

import re
from datetime import datetime, timezone
from typing import Tuple


def generate_title(content: str, max_words: int = 7, max_chars: int = 50) -> str:
    """
    Generate a human-readable title from the first few words or lines of copied content.
    Preserves meaningful tokens while truncating cleanly with an ellipsis.
    """
    if not content:
        return "Untitled Snippet"

    # Find the first non-empty line
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return "Untitled Snippet"

    first_line = lines[0]

    # Split into words (collapsing consecutive whitespace)
    words = first_line.split()
    if not words:
        return "Untitled Snippet"

    selected_words = words[:max_words]
    title = " ".join(selected_words)

    if len(words) > max_words or len(title) > max_chars:
        # Truncate at max_chars if still too long
        if len(title) > max_chars:
            title = title[:max_chars].rstrip()
        title += "…"
    elif len(lines) > 1 and not title.endswith("…"):
        # If there are more lines in the snippet, add ellipsis
        title += "…"

    return title


def validate_snippet(title: str, content: str) -> Tuple[bool, str]:
    """
    Validate that snippet title and content are both non-empty.
    Returns (is_valid, error_message).
    """
    clean_title = (title or "").strip()
    clean_content = (content or "").strip()

    if not clean_title:
        return False, "Title cannot be empty."
    if not clean_content:
        return False, "Content cannot be empty."

    return True, ""


def format_timestamp(ts_string: str) -> str:
    """
    Format an ISO timestamp from Supabase into a friendly localized string.
    """
    if not ts_string:
        return ""

    try:
        # Standard ISO 8601 parsing
        # Handle trailing Z or timezone offsets
        clean_ts = ts_string.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_ts)
        local_dt = dt.astimezone()
        now = datetime.now(timezone.utc).astimezone()

        if local_dt.date() == now.date():
            return f"Today, {local_dt.strftime('%H:%M:%S')}"
        elif (now.date() - local_dt.date()).days == 1:
            return f"Yesterday, {local_dt.strftime('%H:%M:%S')}"
        else:
            return local_dt.strftime("%b %d, %Y %H:%M")
    except Exception:
        # Fallback to returning raw substring if parsing fails
        return ts_string[:19].replace("T", " ")


def get_content_preview(content: str, max_chars: int = 80) -> str:
    """
    Create a clean single-line preview of content for list views.
    """
    if not content:
        return ""

    # Collapse whitespace and newlines into single spaces
    single_line = re.sub(r"\s+", " ", content).strip()
    if len(single_line) > max_chars:
        return single_line[:max_chars].rstrip() + "…"
    return single_line

