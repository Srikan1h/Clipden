# Packaging & Debian Distribution Guide for ClipDen

This guide explains how to build and install the official Debian package (`.deb`) for ClipDen.

---

## 1. Package Overview

- **Package file:** `dist/packages/ClipDen_1.0.0_amd64.deb`
- **Target OS:** Ubuntu / Debian 64-bit (`amd64`)
- **Installation Directory:** `/opt/clipden/`
- **System Command Wrapper:** `/usr/bin/clipden`
- **Desktop Entry:** `/usr/share/applications/clipden.desktop`
- **Application Icon:**
  - Scalable vector: `/usr/share/icons/hicolor/scalable/apps/clipden.svg`
  - 128x128 bitmap: `/usr/share/icons/hicolor/128x128/apps/clipden.png`

---

## 2. Security & User Configuration

- **No hardcoded secrets:** Development `.env` files and local database keys are completely excluded from the package payload.
- **User-specific configuration:** The installed application discovers user settings from:
  1. Linux Secret Service (`keyring`)
  2. `~/.config/clipden/config.env` (user-specific config directory)
  3. Environment variables
- `/opt/clipden/` remains strictly immutable and read-only.

---

## 3. How to Build the Debian Package

### Prerequisites

Ensure required build tools are installed:

```bash
sudo apt update
sudo apt install -y python3 python3-venv binutils dpkg-dev
```

### Build Execution

Run the automated build script:

```bash
./scripts/build_deb.sh
```

The script will:
1. Bundle ClipDen, Tkinter/Tcl resources, and dependencies using PyInstaller in `onedir` mode.
2. Structure the Debian filesystem hierarchy under `build/deb_staging`.
3. Strip any sensitive `.env` files.
4. Calculate `Installed-Size` and bundle control metadata with post-install/post-remove hooks.
5. Generate `dist/packages/ClipDen_1.0.0_amd64.deb`.

---

## 4. How to Install & Run

### Installation

```bash
sudo dpkg -i dist/packages/ClipDen_1.0.0_amd64.deb
```

If any system dependencies (such as `wl-clipboard`) are missing, resolve them with:

```bash
sudo apt-get install -f
```

### Launching ClipDen

Users can launch ClipDen either:
- Directly from the **Ubuntu Application Menu / Dash** (search for `ClipDen`).
- Or from any terminal by typing:
  ```bash
  clipden
  ```

---

## 5. How to Upgrade & Uninstall

### Upgrading

To install a newer version over an existing installation:

```bash
sudo dpkg -i dist/packages/ClipDen_1.0.0_amd64.deb
```

### Uninstallation

To remove ClipDen:

```bash
sudo dpkg -r clipden
```

To purge all package configuration files:

```bash
sudo dpkg -P clipden
```
