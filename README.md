# ClipDen – Linux Desktop Clipboard Manager

> **Tagline:** Everything you copy. One place to keep.

ClipDen is a lightweight, open-source Linux desktop application built for Ubuntu (Wayland / X11) that automatically captures copied text, persists it to your Supabase PostgreSQL database, and allows you to search, edit, delete, and retrieve previously copied snippets.

---

## Features

- **Automatic Clipboard Capture (Wayland-First):**
  - Monitors the system clipboard in the background with zero lag.
  - Automatically captures copied text and persists to Supabase with source `clipboard`.
  - Automatically derives human-readable titles from the first few words or lines.
  - Preserves multiline text, source code snippets, and special characters.
  - Filters out consecutive duplicates and empty/whitespace-only copies.
  - Ignores non-text formats (images, audio, files).
  - Internal copy suppression: copying snippets within ClipDen does not trigger infinite capture loops.
  - Pause and resume monitoring anytime with a single click.

- **Manual Snippet Creation:**
  - Dedicated modal dialog with inline validation (ensures non-empty title and content).
  - Saved with source marked as `manual` and tracked with UTC timestamps.

- **Browsing & Management:**
  - Real-time search by keyword across titles and content.
  - Filter by source (`All`, `Clipboard`, `Manual`).
  - Snippets ordered newest first.
  - Full details view with monospaced code viewer, metadata badges, and formatted local timestamps.
  - Edit existing titles and content with `updated_at` tracking.
  - Delete with safety confirmation dialog.
  - One-click "Copy to Clipboard" with toast confirmation.

- **Supabase Cloud Backend:**
  - PostgreSQL persistent storage with Row Level Security (RLS) enabled.
  - Support for Supabase Python SDK and secure system keyring session storage.
  - Verified against Supabase Database Advisors (Security, Performance, Health).

---

## Technology Stack

- **GUI Framework:** Python 3 + Tkinter / ttk (styled with Ubuntu modern theme)
- **Backend / Storage:** Supabase PostgreSQL + Supabase Python SDK
- **Clipboard Management:** `wl-clipboard` (`wl-paste`, `wl-copy`) and `pyperclip`
- **Concurrency:** Python `threading` with thread-safe `queue.Queue` for UI dispatch and background sync
- **Security & Storage:** Python `keyring` (SecretService) and `python-dotenv`
- **Testing:** `pytest` unit and integration test suite

---

## Database Schema

```sql
CREATE TABLE public.snippets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('manual', 'clipboard')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid()
);

-- Optimized indexes
CREATE INDEX idx_snippets_created_at_desc ON public.snippets (created_at DESC);
CREATE INDEX idx_snippets_user_id ON public.snippets (user_id);

-- Row Level Security
ALTER TABLE public.snippets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow select snippets" ON public.snippets FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Allow insert snippets" ON public.snippets FOR INSERT TO anon, authenticated WITH CHECK (true);
CREATE POLICY "Allow update snippets" ON public.snippets FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow delete snippets" ON public.snippets FOR DELETE TO anon, authenticated USING (true);

GRANT ALL ON TABLE public.snippets TO anon, authenticated, service_role;
```

---

## Installation & Setup

### 1. Prerequisites (Ubuntu Linux)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-tk wl-clipboard
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Set your Supabase credentials in `.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-publishable-key
CLIPBOARD_POLL_INTERVAL=0.35
```

### 3. Setup Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest
```

---

## Running ClipDen

Use the included launcher script:

```bash
./run_clipden.sh
```

Or run via Python directly:

```bash
./.venv/bin/python main.py
```

### Desktop Entry

To integrate ClipDen into your Ubuntu Application menu:

```bash
cp clipden.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

---

## Running Tests

Run the test suite:

```bash
./.venv/bin/pytest -v
```
