"""
Background clipboard monitor for Ubuntu Wayland.
Captures text copied from other applications, filters out duplicates,
ignores images/files, avoids self-captures from ClipDen, and enqueues
snippets for persistence to Supabase.
"""

import atexit
import hashlib
import os
import queue
import shutil
import subprocess
import threading
import time
from typing import Callable, Optional, Set
import pyperclip

from clipden.config import config
from clipden.utils import generate_title


class ClipboardMonitor:
    def __init__(
        self,
        on_snippet_saved: Optional[Callable[[dict], None]] = None,
        on_status_change: Optional[Callable[[bool], None]] = None,
    ):
        self._on_snippet_saved = on_snippet_saved
        self._on_status_change = on_status_change

        self._queue: queue.Queue = queue.Queue()
        self._is_running = False
        self._is_paused = False
        self._lock = threading.Lock()

        # Deduplication and internal copy tracking
        self._last_content_hash: Optional[str] = None
        self._internal_hashes: Set[str] = set()

        # Threads and control events
        self._monitor_thread: Optional[threading.Thread] = None
        self._processor_thread: Optional[threading.Thread] = None
        self._watch_proc: Optional[subprocess.Popen] = None
        self._stop_event = threading.Event()
        self._monitor_stop_event = threading.Event()

        # Optional custom clipboard reader (e.g. from Tkinter main thread)
        self._clipboard_reader: Optional[Callable[[], Optional[str]]] = None

        # Database service reference (injected or imported)
        self._db_service = None

        # Clean up on process exit
        atexit.register(self.stop)

    def set_db_service(self, db_service) -> None:
        self._db_service = db_service

    def set_clipboard_reader(self, reader: Callable[[], Optional[str]]) -> None:
        """Register a custom clipboard reader to avoid spawning subprocesses."""
        self._clipboard_reader = reader

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    @property
    def is_worker_alive(self) -> bool:
        """Check if the background monitoring worker thread is currently active."""
        return bool(self._monitor_thread and self._monitor_thread.is_alive())

    def _hash_content(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()

    def copy_to_system_clipboard(self, text: str) -> bool:
        """
        Copy text to the system clipboard while marking it as an internal copy
        so ClipDen's monitor will not re-capture it.
        """
        if not text:
            return False

        h = self._hash_content(text)
        with self._lock:
            self._internal_hashes.add(h)
            self._last_content_hash = h

        # Perform copy via wl-copy (Wayland) or pyperclip fallback
        try:
            if shutil.which("wl-copy"):
                proc = subprocess.Popen(
                    ["wl-copy", "--type", "text/plain"],
                    stdin=subprocess.PIPE,
                    text=True,
                )
                proc.communicate(input=text)
                return proc.returncode == 0
            else:
                pyperclip.copy(text)
                return True
        except Exception as e:
            print(f"[ClipboardMonitor] Error copying to clipboard: {e}")
            try:
                pyperclip.copy(text)
                return True
            except Exception:
                return False

    def _read_wayland_clipboard(self) -> Optional[str]:
        """
        Read plain text from Wayland clipboard using a single wl-paste call.
        Returns None if clipboard is empty, non-text (e.g. image, file), or error.
        """
        if not shutil.which("wl-paste"):
            try:
                txt = pyperclip.paste()
                return txt if txt and txt.strip() else None
            except Exception:
                return None

        try:
            # Single call to wl-paste requesting text directly, avoiding redundant --list-types
            res = subprocess.run(
                ["wl-paste", "-n", "-t", "text"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=1.0,
            )
            if res.returncode == 0 and res.stdout:
                return res.stdout
            return None
        except Exception:
            return None

    def _read_clipboard(self) -> Optional[str]:
        """Read clipboard using custom reader if set, else fallback to wayland."""
        if self._clipboard_reader:
            try:
                return self._clipboard_reader()
            except Exception:
                return None
        return self._read_wayland_clipboard()

    def start(self) -> None:
        """Start background clipboard monitoring and processor threads."""
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            self._is_paused = False
            self._stop_event.clear()
            self._monitor_stop_event.clear()

        # Prime the current clipboard content so existing text is not auto-captured on startup
        current_clip = self._read_clipboard()
        if current_clip:
            self._last_content_hash = self._hash_content(current_clip)

        # Start queue processor thread
        if not self._processor_thread or not self._processor_thread.is_alive():
            self._processor_thread = threading.Thread(
                target=self._process_queue_loop,
                daemon=True,
                name="ClipDen-Processor",
            )
            self._processor_thread.start()

        # Start exactly one watcher thread
        self._start_monitor_worker()

        if self._on_status_change:
            self._on_status_change(True)

    def _start_monitor_worker(self) -> None:
        """Ensure exactly one monitoring worker thread is active (caller must hold lock or verify state)."""
        if not self._monitor_thread or not self._monitor_thread.is_alive():
            self._monitor_stop_event.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="ClipDen-Watcher",
            )
            self._monitor_thread.start()

    def pause(self) -> None:
        """Pause clipboard monitoring and cleanly stop the monitoring worker thread."""
        thread_to_join: Optional[threading.Thread] = None
        with self._lock:
            if self._is_paused:
                return
            self._is_paused = True
            self._monitor_stop_event.set()
            if self._monitor_thread and self._monitor_thread.is_alive():
                thread_to_join = self._monitor_thread
            self._monitor_thread = None

        if thread_to_join and threading.current_thread() != thread_to_join:
            thread_to_join.join(timeout=1.0)

        if self._on_status_change:
            self._on_status_change(False)

    def resume(self) -> None:
        """Resume clipboard monitoring and start exactly one monitoring worker thread."""
        with self._lock:
            if not self._is_paused and self._monitor_thread and self._monitor_thread.is_alive():
                # Already active with worker running
                return

            self._is_paused = False
            self._is_running = True
            self._monitor_stop_event.clear()

            # Refresh last seen hash so we don't capture what was copied during pause if user didn't want it
            current_clip = self._read_clipboard()
            if current_clip:
                self._last_content_hash = self._hash_content(current_clip)

            # Ensure processor thread is running
            if not self._processor_thread or not self._processor_thread.is_alive():
                self._processor_thread = threading.Thread(
                    target=self._process_queue_loop,
                    daemon=True,
                    name="ClipDen-Processor",
                )
                self._processor_thread.start()

            # Start exactly one monitoring worker
            self._start_monitor_worker()

        if self._on_status_change:
            self._on_status_change(True)

    def toggle_pause(self) -> bool:
        """Toggle pause state. Returns new active state (True = active, False = paused)."""
        if self._is_paused:
            self.resume()
            return True
        else:
            self.pause()
            return False

    def stop(self) -> None:
        """Stop all monitoring threads and terminate child processes cleanly."""
        thread_to_join: Optional[threading.Thread] = None
        with self._lock:
            if not self._is_running and not self._monitor_thread:
                return
            self._is_running = False
            self._is_paused = False
            self._stop_event.set()
            self._monitor_stop_event.set()
            if self._monitor_thread and self._monitor_thread.is_alive():
                thread_to_join = self._monitor_thread
            self._monitor_thread = None

        if thread_to_join and threading.current_thread() != thread_to_join:
            thread_to_join.join(timeout=1.0)

        if self._watch_proc:
            try:
                self._watch_proc.terminate()
                self._watch_proc.wait(timeout=1.0)
            except Exception:
                try:
                    self._watch_proc.kill()
                except Exception:
                    pass
            self._watch_proc = None

        if self._on_status_change:
            self._on_status_change(False)

    def _handle_new_clipboard_text(self, text: str) -> None:
        """Evaluate new clipboard text and enqueue if valid."""
        if not text:
            return

        clean_text = text.strip()
        if not clean_text:
            # Ignore empty or whitespace-only content
            return

        h = self._hash_content(text)

        with self._lock:
            if self._is_paused:
                return

            # Check if this was caused by ClipDen's own copy operation
            if h in self._internal_hashes:
                self._internal_hashes.discard(h)
                self._last_content_hash = h
                return

            # Check for consecutive duplicate entries
            if h == self._last_content_hash:
                return

            self._last_content_hash = h

        # Generate human-readable title from first few words
        title = generate_title(text)

        # Enqueue item for persistence
        self._queue.put({"title": title, "content": text, "source": "clipboard"})

    def _monitor_loop(self) -> None:
        """
        Background watcher loop.
        Monitors clipboard changes on Wayland.
        """
        poll_interval = config.poll_interval

        while not self._stop_event.is_set() and not self._monitor_stop_event.is_set():
            try:
                if not self._is_paused:
                    clip_text = self._read_clipboard()
                    if clip_text:
                        self._handle_new_clipboard_text(clip_text)
            except Exception as e:
                print(f"[ClipboardMonitor] Loop error: {e}")

            # Sleep in small slices to respond promptly to stop events
            slices = int(poll_interval / 0.05) if poll_interval > 0.05 else 1
            for _ in range(slices):
                if self._stop_event.is_set() or self._monitor_stop_event.is_set():
                    break
                time.sleep(0.05)

    def _process_queue_loop(self) -> None:
        """
        Processes captured snippets from the thread-safe queue and saves them to Supabase.
        """
        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                if self._db_service:
                    record = self._db_service.create_snippet(
                        title=item["title"],
                        content=item["content"],
                        source=item["source"],
                    )
                    if self._on_snippet_saved:
                        self._on_snippet_saved(record)
                else:
                    print("[ClipboardMonitor] Database service not attached. Item discarded.")
            except Exception as e:
                print(f"[ClipboardMonitor] Error saving captured snippet: {e}")
            finally:
                self._queue.task_done()
