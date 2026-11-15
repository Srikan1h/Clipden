"""
Main Desktop Application Window for ClipDen.
Provides real-time clipboard synchronization, snippet browsing, search,
full content inspection, editing, and manual snippet creation.
"""

import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, Dict, List, Optional

from clipden.clipboard_monitor import ClipboardMonitor
from clipden.database import db_service
from clipden.ui.settings_dialog import SettingsDialog
from clipden.ui.snippet_dialog import SnippetDialog
from clipden.ui.styles import COLORS, apply_styles
from clipden.utils import format_timestamp, get_content_preview


class ClipDenApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ClipDen – Linux Clipboard Manager")
        self.root.geometry("1000x680")
        self.root.minsize(800, 500)
        self.root.configure(bg=COLORS["bg_main"])

        # Thread-safe UI dispatch queue
        self.ui_queue: queue.Queue = queue.Queue()
        self._is_shutting_down = False
        self._schedule_ui_queue_processor()

        # Setup styling
        self.style = apply_styles(self.root)

        # State
        self.snippets: List[Dict[str, Any]] = []
        self.selected_snippet: Optional[Dict[str, Any]] = None
        self._search_debounce_timer: Optional[threading.Timer] = None
        self._clear_msg_id: Optional[str] = None
        self._cached_clipboard_text: Optional[str] = None

        # Clipboard Monitor
        self.monitor = ClipboardMonitor(
            on_snippet_saved=self._on_snippet_captured_callback,
            on_status_change=self._on_monitor_status_change_callback,
        )
        self.monitor.set_db_service(db_service)
        self.monitor.set_clipboard_reader(self._get_clipboard_from_main_thread)

        # Build UI layout
        self._build_header()
        self._build_toolbar()
        self._build_main_panes()
        self._build_status_bar()

        # Handle window close cleanly
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda _: self.open_new_snippet_dialog())
        self.root.bind("<Control-r>", lambda _: self.refresh_snippets())
        self.root.bind("<Control-f>", lambda _: self.search_entry.focus_set())

        # Start initial load and background monitoring
        self.refresh_snippets()
        self.monitor.start()

    def _get_clipboard_from_main_thread(self) -> Optional[str]:
        return self._cached_clipboard_text

    def _schedule_ui_queue_processor(self) -> None:
        """Process dispatched UI calls and sample clipboard safely on the Tkinter main thread."""
        while not self.ui_queue.empty():
            try:
                task = self.ui_queue.get_nowait()
                task()
            except Exception as e:
                print(f"[ClipDen] UI dispatch error: {e}")

        # Sample clipboard on the main thread without spawning external subprocesses
        if hasattr(self, "monitor") and not self.monitor.is_paused and not self._is_shutting_down:
            try:
                self._cached_clipboard_text = self.root.clipboard_get()
            except Exception:
                self._cached_clipboard_text = None

        if not self._is_shutting_down:
            self.root.after(40, self._schedule_ui_queue_processor)

    def dispatch_to_ui(self, func: Callable[[], None]) -> None:
        """Enqueue a callable to be executed safely on the Tkinter main thread."""
        self.ui_queue.put(func)

    def _build_header(self) -> None:
        header_frame = ttk.Frame(self.root, padding=(16, 12, 16, 8), style="Main.TFrame")
        header_frame.pack(fill=tk.X)

        # Brand Title & Tagline
        brand_frame = ttk.Frame(header_frame, style="Main.TFrame")
        brand_frame.pack(side=tk.LEFT)

        title_lbl = ttk.Label(
            brand_frame,
            text="Clipden",
            font=("Ubuntu", 16, "bold"),
            foreground=COLORS["primary"],
            background=COLORS["bg_main"],
        )
        title_lbl.pack(side=tk.LEFT)

        tagline_lbl = ttk.Label(
            brand_frame,
            text="  •  Everything you copy. One place to keep.",
            font=("Ubuntu", 10),
            foreground=COLORS["text_muted"],
            background=COLORS["bg_main"],
        )
        tagline_lbl.pack(side=tk.LEFT, pady=(3, 0))

        # Top-right quick actions
        actions_frame = ttk.Frame(header_frame, style="Main.TFrame")
        actions_frame.pack(side=tk.RIGHT)

        self.pause_resume_btn = ttk.Button(
            actions_frame,
            text="⏸ Pause",
            style="Secondary.TButton",
            command=self._toggle_monitoring,
        )
        self.pause_resume_btn.pack(side=tk.LEFT, padx=(0, 8))

        settings_btn = ttk.Button(
            actions_frame,
            text="⚙ Settings",
            style="Secondary.TButton",
            command=self.open_settings_dialog,
        )
        settings_btn.pack(side=tk.LEFT)

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self.root, padding=(16, 4, 16, 10), style="Toolbar.TFrame")
        toolbar.pack(fill=tk.X)

        # New snippet button
        new_btn = ttk.Button(
            toolbar,
            text="+ New Snippet",
            style="Primary.TButton",
            command=self.open_new_snippet_dialog,
        )
        new_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Refresh button
        refresh_btn = ttk.Button(
            toolbar,
            text="↻ Refresh",
            style="Secondary.TButton",
            command=self.refresh_snippets,
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 14))

        # Search bar
        search_lbl = ttk.Label(
            toolbar,
            text="Search:",
            font=("Ubuntu", 10, "bold"),
            background=COLORS["bg_main"],
        )
        search_lbl.pack(side=tk.LEFT, padx=(0, 6))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)

        self.search_entry = ttk.Entry(
            toolbar,
            textvariable=self.search_var,
            width=28,
            font=("Ubuntu", 10),
        )
        self.search_entry.pack(side=tk.LEFT, padx=(0, 8))

        clear_search_btn = ttk.Button(
            toolbar,
            text="✕",
            width=3,
            style="Secondary.TButton",
            command=lambda: self.search_var.set(""),
        )
        clear_search_btn.pack(side=tk.LEFT, padx=(0, 14))

        # Source filter dropdown
        filter_lbl = ttk.Label(
            toolbar,
            text="Source:",
            font=("Ubuntu", 10, "bold"),
            background=COLORS["bg_main"],
        )
        filter_lbl.pack(side=tk.LEFT, padx=(0, 6))

        self.filter_var = tk.StringVar(value="All")
        self.filter_cb = ttk.Combobox(
            toolbar,
            textvariable=self.filter_var,
            values=["All", "Clipboard", "Manual"],
            state="readonly",
            width=12,
            font=("Ubuntu", 10),
        )
        self.filter_cb.pack(side=tk.LEFT)
        self.filter_cb.bind("<<ComboboxSelected>>", lambda _: self.refresh_snippets())

    def _build_main_panes(self) -> None:
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        # --- LEFT PANE (Snippets List) ---
        left_frame = ttk.Frame(paned, style="Sidebar.TFrame")
        paned.add(left_frame, weight=3)

        tree_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL)
        self.tree = ttk.Treeview(
            left_frame,
            columns=("title", "source", "timestamp"),
            show="headings",
            style="Snippets.Treeview",
            yscrollcommand=tree_scroll.set,
            selectmode="browse",
        )
        tree_scroll.config(command=self.tree.yview)

        self.tree.heading("title", text="Snippet Title / Preview")
        self.tree.heading("source", text="Source")
        self.tree.heading("timestamp", text="Date & Time")

        self.tree.column("title", width=260, anchor=tk.W)
        self.tree.column("source", width=85, anchor=tk.CENTER)
        self.tree.column("timestamp", width=140, anchor=tk.E)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Delete>", lambda _: self.delete_selected_snippet())

        # --- RIGHT PANE (Snippet Details) ---
        right_frame = ttk.Frame(paned, padding=16, style="Card.TFrame")
        paned.add(right_frame, weight=4)

        # Header with Title and Badges
        self.detail_header_frame = ttk.Frame(right_frame, style="Card.TFrame")
        self.detail_header_frame.pack(fill=tk.X, pady=(0, 8))

        self.detail_title = ttk.Label(
            self.detail_header_frame,
            text="Select a snippet to view details",
            font=("Ubuntu", 13, "bold"),
            foreground=COLORS["text_main"],
            background=COLORS["bg_card"],
            wraplength=380,
        )
        self.detail_title.pack(anchor=tk.W, fill=tk.X)

        self.detail_meta = ttk.Label(
            self.detail_header_frame,
            text="",
            font=("Ubuntu", 9),
            foreground=COLORS["text_muted"],
            background=COLORS["bg_card"],
        )
        self.detail_meta.pack(anchor=tk.W, pady=(4, 0))

        # Action Buttons bar
        self.actions_bar = ttk.Frame(right_frame, style="Card.TFrame")
        self.actions_bar.pack(fill=tk.X, pady=(4, 10))

        self.copy_btn = ttk.Button(
            self.actions_bar,
            text="📋 Copy to Clipboard",
            style="Primary.TButton",
            command=self.copy_selected_to_clipboard,
            state=tk.DISABLED,
        )
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.edit_btn = ttk.Button(
            self.actions_bar,
            text="✏ Edit",
            style="Secondary.TButton",
            command=self.edit_selected_snippet,
            state=tk.DISABLED,
        )
        self.edit_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.delete_btn = ttk.Button(
            self.actions_bar,
            text="🗑 Delete",
            style="Danger.TButton",
            command=self.delete_selected_snippet,
            state=tk.DISABLED,
        )
        self.delete_btn.pack(side=tk.LEFT)

        # Content Text Box with Scrollbar
        content_frame = ttk.Frame(right_frame, style="Card.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)

        content_scroll = ttk.Scrollbar(content_frame, orient=tk.VERTICAL)
        self.content_view = tk.Text(
            content_frame,
            wrap=tk.WORD,
            font=("Monospace", 10),
            bg="#ffffff",
            fg=COLORS["text_main"],
            relief=tk.SOLID,
            borderwidth=1,
            yscrollcommand=content_scroll.set,
            padx=10,
            pady=10,
        )
        content_scroll.config(command=self.content_view.yview)

        self.content_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        content_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_view.config(state=tk.DISABLED)

    def _build_status_bar(self) -> None:
        status_bar = ttk.Frame(self.root, padding=(16, 4, 16, 6), style="Main.TFrame")
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Left status indicators
        self.conn_status_lbl = ttk.Label(
            status_bar,
            text="● Supabase: Checking...",
            style="Status.TLabel",
        )
        self.conn_status_lbl.pack(side=tk.LEFT, padx=(0, 16))

        self.monitor_status_lbl = ttk.Label(
            status_bar,
            text="● Monitoring: Active",
            style="Status.TLabel",
        )
        self.monitor_status_lbl.pack(side=tk.LEFT, padx=(0, 16))

        # Flash notification message
        self.flash_msg_lbl = ttk.Label(
            status_bar,
            text="",
            font=("Ubuntu", 9, "bold"),
            foreground=COLORS["primary"],
            background=COLORS["bg_main"],
        )
        self.flash_msg_lbl.pack(side=tk.LEFT, padx=(0, 16))

        # Right item count
        self.count_lbl = ttk.Label(
            status_bar,
            text="0 snippets",
            style="Status.TLabel",
        )
        self.count_lbl.pack(side=tk.RIGHT)

    def show_flash_message(self, text: str, duration_ms: int = 3000) -> None:
        """Display a temporary toast-like notification in the status bar."""
        if self._clear_msg_id:
            try:
                self.root.after_cancel(self._clear_msg_id)
            except Exception:
                pass
        self.flash_msg_lbl.config(text=text)
        self._clear_msg_id = self.root.after(duration_ms, lambda: self.flash_msg_lbl.config(text=""))

    def _toggle_monitoring(self) -> None:
        self.monitor.toggle_pause()

    def _update_monitoring_ui(self, is_active: bool) -> None:
        if is_active:
            self.pause_resume_btn.config(text="⏸ Pause")
            self.monitor_status_lbl.config(
                text="⚡ Monitoring: Active",
                foreground=COLORS["success"],
            )
            self.show_flash_message("Clipboard monitoring resumed.")
        else:
            self.pause_resume_btn.config(text="▶ Resume")
            self.monitor_status_lbl.config(
                text="⏸ Monitoring: Paused",
                foreground=COLORS["warning"],
            )
            self.show_flash_message("Clipboard monitoring paused.")

    def _on_monitor_status_change_callback(self, is_active: bool) -> None:
        self.dispatch_to_ui(lambda: self._update_monitoring_ui(is_active))

    def _on_snippet_captured_callback(self, snippet: dict) -> None:
        def on_ui():
            self.show_flash_message(f"Captured: {snippet.get('title', 'New Snippet')}")
            self.refresh_snippets(auto_select_first=False)

        self.dispatch_to_ui(on_ui)

    def _on_search_changed(self, *_) -> None:
        if self._search_debounce_timer:
            self._search_debounce_timer.cancel()
        self._search_debounce_timer = threading.Timer(0.25, lambda: self.dispatch_to_ui(self.refresh_snippets))
        self._search_debounce_timer.start()

    def refresh_snippets(self, auto_select_first: bool = False) -> None:
        """Fetch snippets from Supabase on a background thread and update the list."""
        search_query = self.search_var.get().strip()
        source_val = self.filter_var.get().lower()
        source_filter = source_val if source_val in ("clipboard", "manual") else None

        def worker():
            try:
                data = db_service.get_snippets(
                    search_query=search_query if search_query else None,
                    source_filter=source_filter,
                )
                self.dispatch_to_ui(lambda: self._apply_snippets_to_ui(data, auto_select_first))
                self.dispatch_to_ui(
                    lambda: self.conn_status_lbl.config(
                        text="● Supabase: Connected",
                        foreground=COLORS["success"],
                    )
                )
            except Exception as e:
                print(f"[ClipDen] Fetch error: {e}")
                self.dispatch_to_ui(
                    lambda: self.conn_status_lbl.config(
                        text="● Supabase Error",
                        foreground=COLORS["danger"],
                    )
                )

        threading.Thread(target=worker, daemon=True).start()

    def _apply_snippets_to_ui(self, items: List[Dict[str, Any]], auto_select_first: bool = False) -> None:
        self.snippets = items

        # Preserve current selection if possible
        current_selected_id = self.selected_snippet.get("id") if self.selected_snippet else None

        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        matched_item_iid = None
        for s in items:
            s_id = s.get("id")
            title = s.get("title") or "Untitled"
            preview = get_content_preview(s.get("content", ""))
            display_title = f"{title}  —  {preview}" if preview and preview != title else title
            source = (s.get("source") or "clipboard").capitalize()
            ts = format_timestamp(s.get("created_at", ""))

            iid = self.tree.insert("", tk.END, iid=s_id, values=(display_title, source, ts))
            if s_id == current_selected_id:
                matched_item_iid = iid

        # Update count label
        self.count_lbl.config(text=f"{len(items)} snippet{'s' if len(items) != 1 else ''}")

        # Restore selection or auto-select
        if matched_item_iid:
            self.tree.selection_set(matched_item_iid)
            self.tree.see(matched_item_iid)
        elif auto_select_first and items:
            first_iid = items[0].get("id")
            self.tree.selection_set(first_iid)
            self.tree.see(first_iid)
        elif not self.tree.selection():
            self._clear_detail_view()

    def _on_tree_select(self, _=None) -> None:
        selected_iids = self.tree.selection()
        if not selected_iids:
            self._clear_detail_view()
            return

        s_id = selected_iids[0]
        snippet = next((s for s in self.snippets if s.get("id") == s_id), None)
        if not snippet:
            self._clear_detail_view()
            return

        self.selected_snippet = snippet
        self._populate_detail_view(snippet)

    def _populate_detail_view(self, snippet: Dict[str, Any]) -> None:
        self.detail_title.config(text=snippet.get("title", "Untitled Snippet"))

        source = (snippet.get("source") or "clipboard").upper()
        created = format_timestamp(snippet.get("created_at", ""))
        updated = format_timestamp(snippet.get("updated_at", ""))

        meta_text = f"Source: {source}   |   Created: {created}"
        if updated and updated != created:
            meta_text += f"   |   Updated: {updated}"
        self.detail_meta.config(text=meta_text)

        # Update text content
        self.content_view.config(state=tk.NORMAL)
        self.content_view.delete("1.0", tk.END)
        self.content_view.insert("1.0", snippet.get("content", ""))
        self.content_view.config(state=tk.DISABLED)

        # Enable action buttons
        self.copy_btn.config(state=tk.NORMAL)
        self.edit_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)

    def _clear_detail_view(self) -> None:
        self.selected_snippet = None
        self.detail_title.config(text="Select a snippet to view details")
        self.detail_meta.config(text="")
        self.content_view.config(state=tk.NORMAL)
        self.content_view.delete("1.0", tk.END)
        self.content_view.config(state=tk.DISABLED)

        self.copy_btn.config(state=tk.DISABLED)
        self.edit_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)

    def copy_selected_to_clipboard(self) -> None:
        """Copy current snippet's content to system clipboard without triggering re-capture."""
        if not self.selected_snippet:
            return

        content = self.selected_snippet.get("content", "")
        if not content:
            return

        success = self.monitor.copy_to_system_clipboard(content)
        if success:
            self.show_flash_message("✓ Copied to clipboard!")
        else:
            self.show_flash_message("Failed to copy to clipboard", duration_ms=4000)

    def open_new_snippet_dialog(self) -> None:
        """Open dialog to manually create a new snippet."""
        def save_worker(title: str, content: str):
            try:
                new_record = db_service.create_snippet(title=title, content=content, source="manual")
                self.dispatch_to_ui(lambda: self.show_flash_message("✓ Snippet created!"))
                self.dispatch_to_ui(lambda: self.refresh_snippets(auto_select_first=True))
            except Exception as e:
                self.dispatch_to_ui(
                    lambda: messagebox.showerror("Save Error", f"Could not create snippet:\n{e}", parent=self.root)
                )

        SnippetDialog(
            parent=self.root,
            title_text="Create New Snippet",
            on_save=lambda t, c: threading.Thread(target=save_worker, args=(t, c), daemon=True).start(),
        )

    def edit_selected_snippet(self) -> None:
        """Open dialog to edit title and content of selected snippet."""
        if not self.selected_snippet:
            return

        snippet_id = self.selected_snippet["id"]

        def save_worker(title: str, content: str):
            try:
                updated_record = db_service.update_snippet(snippet_id=snippet_id, title=title, content=content)
                self.dispatch_to_ui(lambda: self.show_flash_message("✓ Snippet updated!"))
                self.dispatch_to_ui(self.refresh_snippets)
            except Exception as e:
                self.dispatch_to_ui(
                    lambda: messagebox.showerror("Update Error", f"Could not update snippet:\n{e}", parent=self.root)
                )

        SnippetDialog(
            parent=self.root,
            title_text="Edit Snippet",
            initial_title=self.selected_snippet.get("title", ""),
            initial_content=self.selected_snippet.get("content", ""),
            on_save=lambda t, c: threading.Thread(target=save_worker, args=(t, c), daemon=True).start(),
        )

    def delete_selected_snippet(self) -> None:
        """Prompt user and delete selected snippet from Supabase."""
        if not self.selected_snippet:
            return

        title = self.selected_snippet.get("title", "this snippet")
        confirmed = messagebox.askyesno(
            "Delete Snippet",
            f"Are you sure you want to permanently delete:\n\n'{title}'?",
            parent=self.root,
            icon=messagebox.WARNING,
        )
        if not confirmed:
            return

        snippet_id = self.selected_snippet["id"]

        def delete_worker():
            try:
                db_service.delete_snippet(snippet_id)
                self.dispatch_to_ui(lambda: self.show_flash_message("✓ Snippet deleted."))
                self.dispatch_to_ui(self.refresh_snippets)
            except Exception as e:
                self.dispatch_to_ui(
                    lambda: messagebox.showerror("Delete Error", f"Could not delete snippet:\n{e}", parent=self.root)
                )

        threading.Thread(target=delete_worker, daemon=True).start()

    def open_settings_dialog(self) -> None:
        """Open settings dialog to update Supabase configuration."""
        def on_updated(url: str, key: str):
            success, msg = db_service.reload_credentials(url, key)
            if success:
                self.show_flash_message("✓ Supabase reconnected.")
                self.refresh_snippets()
            else:
                self.show_flash_message("✗ Supabase connection failed.")

        SettingsDialog(parent=self.root, on_credentials_updated=on_updated)

    def on_closing(self) -> None:
        """Clean shutdown hook when closing main window."""
        self._is_shutting_down = True
        try:
            self.monitor.stop()
        except Exception:
            pass
        self.root.destroy()
