"""
Tests verifying clean Pause/Resume worker lifecycle, duplicate prevention, and thread management.
"""

import threading
import time
import tkinter as tk
from unittest.mock import MagicMock
from clipden.clipboard_monitor import ClipboardMonitor
from clipden.ui.app import ClipDenApp


def test_pause_stops_worker_and_resume_starts_exactly_one():
    monitor = ClipboardMonitor()
    mock_db = MagicMock()
    monitor.set_db_service(mock_db)

    # 1. Start monitor
    monitor.start()
    assert monitor.is_running is True
    assert monitor.is_paused is False
    assert monitor.is_worker_alive is True
    first_worker = monitor._monitor_thread

    # 2. Pause stops the worker thread cleanly
    monitor.pause()
    assert monitor.is_paused is True
    assert monitor.is_worker_alive is False
    assert monitor._monitor_thread is None

    # 3. Resume starts exactly ONE worker thread
    monitor.resume()
    assert monitor.is_paused is False
    assert monitor.is_worker_alive is True
    second_worker = monitor._monitor_thread
    assert second_worker is not None
    assert second_worker.is_alive()

    # 4. Repeated resume calls are idempotent and do NOT spawn duplicate threads
    monitor.resume()
    monitor.resume()
    assert monitor._monitor_thread is second_worker

    # 5. Clean shutdown
    monitor.stop()
    assert monitor.is_worker_alive is False


def test_repeated_toggle_stability():
    monitor = ClipboardMonitor()
    monitor.start()

    # Rapidly toggle pause and resume 10 times
    for _ in range(10):
        active = monitor.toggle_pause()
        if active:
            assert monitor.is_worker_alive is True
        else:
            assert monitor.is_worker_alive is False

    monitor.stop()
    assert monitor.is_worker_alive is False


def test_gui_toggle_pause_resume():
    root = tk.Tk()
    root.withdraw()
    app = ClipDenApp(root)

    # Pump loop
    for _ in range(5):
        root.update()
        time.sleep(0.02)

    assert app.monitor.is_worker_alive is True
    assert app.pause_resume_btn.cget("text") == "⏸ Pause"

    # Toggle to Pause
    app._toggle_monitoring()
    for _ in range(5):
        root.update()
        time.sleep(0.02)

    assert app.monitor.is_paused is True
    assert app.monitor.is_worker_alive is False
    assert app.pause_resume_btn.cget("text") == "▶ Resume"

    # Toggle to Resume
    app._toggle_monitoring()
    for _ in range(5):
        root.update()
        time.sleep(0.02)

    assert app.monitor.is_paused is False
    assert app.monitor.is_worker_alive is True
    assert app.pause_resume_btn.cget("text") == "⏸ Pause"

    app.on_closing()

