"""
Unit tests for ClipboardMonitor logic.
"""

from unittest.mock import MagicMock
from clipden.clipboard_monitor import ClipboardMonitor


def test_monitor_enqueue_new_text():
    monitor = ClipboardMonitor()
    mock_db = MagicMock()
    mock_db.create_snippet.return_value = {"id": "123", "title": "Test", "content": "Sample text"}
    monitor.set_db_service(mock_db)

    # Initial state
    assert monitor._queue.empty()

    # Feed text
    monitor._handle_new_clipboard_text("Hello ClipDen World")

    # Item should be in queue
    assert not monitor._queue.empty()
    item = monitor._queue.get_nowait()
    assert item["content"] == "Hello ClipDen World"
    assert item["source"] == "clipboard"
    assert "Hello" in item["title"]


def test_monitor_deduplication():
    monitor = ClipboardMonitor()

    # First text
    monitor._handle_new_clipboard_text("Duplicate candidate")
    assert monitor._queue.qsize() == 1

    # Same text consecutively
    monitor._handle_new_clipboard_text("Duplicate candidate")
    assert monitor._queue.qsize() == 1  # Should NOT increase


def test_monitor_empty_text_ignored():
    monitor = ClipboardMonitor()
    monitor._handle_new_clipboard_text("")
    monitor._handle_new_clipboard_text("   \n\t  ")
    assert monitor._queue.empty()


def test_monitor_self_copy_ignored():
    monitor = ClipboardMonitor()

    text = "Secret text copied from within ClipDen"
    # Mark as internal copy
    h = monitor._hash_content(text)
    monitor._internal_hashes.add(h)

    # When monitor sees this text
    monitor._handle_new_clipboard_text(text)
    assert monitor._queue.empty()
    assert h not in monitor._internal_hashes


def test_monitor_pause_resume():
    monitor = ClipboardMonitor()

    monitor.pause()
    assert monitor.is_paused is True

    monitor._handle_new_clipboard_text("Should be ignored while paused")
    assert monitor._queue.empty()

    monitor.resume()
    assert monitor.is_paused is False
