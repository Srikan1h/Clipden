# ClipDen – Linux Desktop Clipboard Manager

> **Tagline:** Everything you copy. One place to keep.

ClipDen is a lightweight, open-source Linux desktop application built for Ubuntu (Wayland / X11) that automatically captures copied text, persists it to your Supabase PostgreSQL database, and allows you to search, edit, delete, and retrieve previously copied snippets.

---

## Connecting ClipDen to Supabase

ClipDen uses your own Supabase project to store clipboard snippets. Your data remains entirely in your database, and ClipDen does not operate a centralized backend.

### Setup

1. Create a free project at [supabase.com](https://supabase.com).
2. Open the **SQL Editor** in your Supabase dashboard.
3. Open [`database/schema.sql`](database/schema.sql) from this repository, copy the complete script, and run it in the SQL Editor.
4. Enable **Anonymous Sign-ins** in the Supabase dashboard under **Authentication → Sign In / Providers**.
5. Open **Project Settings → API Keys**.
6. Copy your **Project URL** and **Publishable Key** (or anon key).
7. Launch ClipDen and enter these credentials in the Settings dialog.

> [!IMPORTANT]
> Use only your Supabase Project URL and Publishable / Anon Key. Never enter your Secret Key or service-role key into ClipDen.

Once connected, ClipDen automatically creates an anonymous authentication session and securely stores your snippets in your own database with user-isolated Row Level Security (RLS).

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

## Database Schema & Row Level Security

The complete database initialization script is available in [`database/schema.sql`](database/schema.sql).

It provisions:
- **`snippets` Table:** Stores captured and manual snippets with `user_id` defaulting to `auth.uid()`.
- **Performance Indexes:** Optimized B-tree indexes for `user_id`, `created_at DESC`, and composite `(user_id, created_at DESC)`.
- **Timestamp Automation:** Trigger using search-path-hardened PL/pgSQL function to update `updated_at`.
- **Strict Row Level Security (RLS):** Policies restricting access so each authenticated user can only view, insert, update, or delete their own snippets (`(SELECT auth.uid()) = user_id`).
- **Least-Privilege Grants:** Revokes permissions from `PUBLIC` and `anon`; grants needed table privileges only to `authenticated`.
- **Verification Assertion:** Automated post-execution check validating that RLS and policy configurations are active.

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

