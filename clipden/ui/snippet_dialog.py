"""
Snippet creation and editing dialog for ClipDen.
Validates required fields (title, content) and returns updated data.
"""

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Callable, Optional, Tuple

from clipden.ui.styles import COLORS
from clipden.utils import validate_snippet


class SnippetDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        title_text: str = "New Snippet",
        initial_title: str = "",
        initial_content: str = "",
        on_save: Optional[Callable[[str, str], None]] = None,
    ):
        super().__init__(parent)
        self.transient(parent)
        self.title(title_text)
        self.geometry("540x520")
        self.minsize(450, 400)
        self.configure(bg=COLORS["bg_main"])

        self._on_save = on_save
        self._saved_data: Optional[Tuple[str, str]] = None

        self._build_ui(initial_title, initial_content)

        # Center dialog relative to parent
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
        self.title_entry.focus_set()

    def _build_ui(self, initial_title: str, initial_content: str) -> None:
        main_frame = ttk.Frame(self, padding=18, style="Main.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title Label & Entry
        title_lbl = ttk.Label(
            main_frame,
            text="Snippet Title *",
            font=("Ubuntu", 10, "bold"),
            background=COLORS["bg_main"],
        )
        title_lbl.pack(anchor=tk.W, pady=(0, 4))

        self.title_var = tk.StringVar(value=initial_title)
        self.title_entry = ttk.Entry(
            main_frame,
            textvariable=self.title_var,
            font=("Ubuntu", 11),
        )
        self.title_entry.pack(fill=tk.X, pady=(0, 14))

        # Content Label & Text Box
        content_lbl = ttk.Label(
            main_frame,
            text="Snippet Content *",
            font=("Ubuntu", 10, "bold"),
            background=COLORS["bg_main"],
        )
        content_lbl.pack(anchor=tk.W, pady=(0, 4))

        self.content_text = ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=("Monospace", 10),
            bg="#ffffff",
            fg=COLORS["text_main"],
            insertbackground=COLORS["text_main"],
            relief=tk.SOLID,
            borderwidth=1,
        )
        self.content_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        if initial_content:
            self.content_text.insert("1.0", initial_content)

        # Error / Validation Label
        self.error_label = ttk.Label(
            main_frame,
            text="",
            foreground=COLORS["danger"],
            font=("Ubuntu", 9, "bold"),
            background=COLORS["bg_main"],
        )
        self.error_label.pack(anchor=tk.W, pady=(0, 10))

        # Button Bar
        btn_frame = ttk.Frame(main_frame, style="Main.TFrame")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        cancel_btn = ttk.Button(
            btn_frame,
            text="Cancel",
            style="Secondary.TButton",
            command=self.destroy,
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(8, 0))

        save_btn = ttk.Button(
            btn_frame,
            text="Save Snippet",
            style="Primary.TButton",
            command=self._handle_save,
        )
        save_btn.pack(side=tk.RIGHT)

        # Keybindings
        self.bind("<Control-Return>", lambda _: self._handle_save())
        self.bind("<Escape>", lambda _: self.destroy())

    def _handle_save(self) -> None:
        title = self.title_var.get()
        content = self.content_text.get("1.0", tk.END).strip()

        is_valid, err_msg = validate_snippet(title, content)
        if not is_valid:
            self.error_label.config(text=err_msg)
            return

        self.error_label.config(text="")
        self._saved_data = (title.strip(), content)

        if self._on_save:
            self._on_save(title.strip(), content)

        self.destroy()

    @property
    def result(self) -> Optional[Tuple[str, str]]:
        return self._saved_data

