"""
Theme and styling definitions for ClipDen Tkinter/ttk interface.
"""

import tkinter as tk
from tkinter import ttk

# Modern color palette inspired by Ubuntu desktop
COLORS = {
    "bg_main": "#f7f7f9",
    "bg_sidebar": "#ffffff",
    "bg_card": "#ffffff",
    "text_main": "#1e1e24",
    "text_muted": "#6c757d",
    "text_light": "#ffffff",
    "primary": "#e95420",  # Ubuntu Orange
    "primary_hover": "#d14817",
    "primary_active": "#b83e14",
    "secondary": "#77216f",  # Ubuntu Aubergine
    "accent_blue": "#2072b8",
    "success": "#2e7d32",
    "warning": "#ed6c02",
    "danger": "#d32f2f",
    "border": "#e0e0e0",
    "selected": "#ffeedd",
    "selected_border": "#e95420",
    "badge_clipboard": "#e8f0fe",
    "badge_clipboard_fg": "#1a73e8",
    "badge_manual": "#fef7e0",
    "badge_manual_fg": "#b06000",
}


def apply_styles(root: tk.Tk) -> ttk.Style:
    """Apply modern ttk theme styles."""
    style = ttk.Style(root)
    # Use clam or default as the base for custom colors
    available_themes = style.theme_names()
    if "clam" in available_themes:
        style.theme_use("clam")

    # General frames
    style.configure("Main.TFrame", background=COLORS["bg_main"])
    style.configure("Sidebar.TFrame", background=COLORS["bg_sidebar"])
    style.configure("Card.TFrame", background=COLORS["bg_card"], relief="flat")
    style.configure("Toolbar.TFrame", background=COLORS["bg_main"])

    # Labels
    style.configure(
        "Header.TLabel",
        background=COLORS["bg_main"],
        foreground=COLORS["text_main"],
        font=("Ubuntu", 14, "bold"),
    )
    style.configure(
        "Subheader.TLabel",
        background=COLORS["bg_main"],
        foreground=COLORS["text_muted"],
        font=("Ubuntu", 10),
    )
    style.configure(
        "Status.TLabel",
        background=COLORS["bg_main"],
        foreground=COLORS["text_muted"],
        font=("Ubuntu", 9),
    )
    style.configure(
        "CardTitle.TLabel",
        background=COLORS["bg_card"],
        foreground=COLORS["text_main"],
        font=("Ubuntu", 12, "bold"),
    )
    style.configure(
        "CardMeta.TLabel",
        background=COLORS["bg_card"],
        foreground=COLORS["text_muted"],
        font=("Ubuntu", 9),
    )

    # Primary Action Button
    style.configure(
        "Primary.TButton",
        background=COLORS["primary"],
        foreground=COLORS["text_light"],
        font=("Ubuntu", 10, "bold"),
        padding=(12, 6),
        borderwidth=0,
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLORS["primary_hover"]), ("pressed", COLORS["primary_active"])],
        foreground=[("disabled", "#a0a0a0")],
    )

    # Standard / Secondary Button
    style.configure(
        "Secondary.TButton",
        background="#e8eaed",
        foreground=COLORS["text_main"],
        font=("Ubuntu", 10),
        padding=(10, 5),
        borderwidth=0,
    )
    style.map(
        "Secondary.TButton",
        background=[("active", "#dadce0"), ("pressed", "#bdc1c6")],
    )

    # Danger Button (e.g. Delete)
    style.configure(
        "Danger.TButton",
        background="#feebe9",
        foreground=COLORS["danger"],
        font=("Ubuntu", 10, "bold"),
        padding=(10, 5),
        borderwidth=0,
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#fad2cf"), ("pressed", "#f8b4af")],
    )

    # Treeview Styling
    style.configure(
        "Snippets.Treeview",
        background="#ffffff",
        foreground=COLORS["text_main"],
        fieldbackground="#ffffff",
        rowheight=32,
        font=("Ubuntu", 10),
        borderwidth=0,
    )
    style.map(
        "Snippets.Treeview",
        background=[("selected", COLORS["selected"])],
        foreground=[("selected", COLORS["text_main"])],
    )
    style.configure(
        "Snippets.Treeview.Heading",
        background="#f1f3f4",
        foreground=COLORS["text_main"],
        font=("Ubuntu", 10, "bold"),
        padding=(6, 6),
        borderwidth=1,
    )

    return style
