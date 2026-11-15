"""
Settings and Supabase configuration dialog for ClipDen.
Allows configuring project URL and API key, testing connectivity, and persisting to Keyring/.env.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from clipden.config import config
from clipden.ui.styles import COLORS


class SettingsDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        on_credentials_updated: Optional[Callable[[str, str], None]] = None,
    ):
        super().__init__(parent)
        self.transient(parent)
        self.title("ClipDen Settings")
        self.geometry("560x360")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg_main"])

        self._on_credentials_updated = on_credentials_updated
        self._build_ui()

        # Center relative to parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = self.winfo_width()
        h = self.winfo_height()
        x = max(0, px + (pw - w) // 2)
        y = max(0, py + (ph - h) // 2)
        self.geometry(f"+{x}+{y}")

        self.grab_set()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=20, style="Main.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(
            frame,
            text="Supabase Cloud Configuration",
            font=("Ubuntu", 12, "bold"),
            background=COLORS["bg_main"],
        )
        header.pack(anchor=tk.W, pady=(0, 6))

        desc = ttk.Label(
            frame,
            text="ClipDen securely syncs your clipboard snippets with your Supabase database.",
            font=("Ubuntu", 9),
            foreground=COLORS["text_muted"],
            background=COLORS["bg_main"],
        )
        desc.pack(anchor=tk.W, pady=(0, 16))

        # URL
        url_lbl = ttk.Label(
            frame,
            text="Project URL",
            font=("Ubuntu", 10, "bold"),
            background=COLORS["bg_main"],
        )
        url_lbl.pack(anchor=tk.W, pady=(0, 4))

        self.url_var = tk.StringVar(value=config.supabase_url or "")
        self.url_entry = ttk.Entry(frame, textvariable=self.url_var, font=("Ubuntu", 10))
        self.url_entry.pack(fill=tk.X, pady=(0, 12))

        # API Key
        key_lbl = ttk.Label(
            frame,
            text="Publishable / Anon API Key",
            font=("Ubuntu", 10, "bold"),
            background=COLORS["bg_main"],
        )
        key_lbl.pack(anchor=tk.W, pady=(0, 4))

        self.key_var = tk.StringVar(value=config.supabase_key or "")
        self.key_entry = ttk.Entry(frame, textvariable=self.key_var, show="•", font=("Ubuntu", 10))
        self.key_entry.pack(fill=tk.X, pady=(0, 14))

        # Status feedback label
        self.status_lbl = ttk.Label(
            frame,
            text="",
            font=("Ubuntu", 9),
            background=COLORS["bg_main"],
        )
        self.status_lbl.pack(anchor=tk.W, pady=(0, 10))

        # Buttons
        btn_frame = ttk.Frame(frame, style="Main.TFrame")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        close_btn = ttk.Button(
            btn_frame,
            text="Cancel",
            style="Secondary.TButton",
            command=self.destroy,
        )
        close_btn.pack(side=tk.RIGHT, padx=(8, 0))

        save_btn = ttk.Button(
            btn_frame,
            text="Save Settings",
            style="Primary.TButton",
            command=self._handle_save,
        )
        save_btn.pack(side=tk.RIGHT, padx=(8, 0))

        test_btn = ttk.Button(
            btn_frame,
            text="Test Connection",
            style="Secondary.TButton",
            command=self._handle_test,
        )
        test_btn.pack(side=tk.LEFT)

    def _handle_test(self) -> None:
        url = self.url_var.get().strip()
        key = self.key_var.get().strip()

        if not url or not key:
            self.status_lbl.config(
                text="Please provide both Project URL and API Key.",
                foreground=COLORS["danger"],
            )
            return

        self.status_lbl.config(text="Testing connection...", foreground=COLORS["text_muted"])
        self.update_idletasks()

        from supabase import create_client

        try:
            client = create_client(url, key)
            res = client.table("snippets").select("id").limit(1).execute()
            self.status_lbl.config(
                text="✓ Connection test successful!",
                foreground=COLORS["success"],
            )
        except Exception as e:
            self.status_lbl.config(
                text=f"✗ Connection failed: {e}",
                foreground=COLORS["danger"],
            )

    def _handle_save(self) -> None:
        url = self.url_var.get().strip()
        key = self.key_var.get().strip()

        if not url or not key:
            messagebox.showwarning(
                "Incomplete Credentials",
                "Both Project URL and API Key are required.",
                parent=self,
            )
            return

        config.save_credentials(url, key, save_to_keyring=True)

        if self._on_credentials_updated:
            self._on_credentials_updated(url, key)

        messagebox.showinfo("Saved", "Supabase credentials updated successfully.", parent=self)
        self.destroy()
