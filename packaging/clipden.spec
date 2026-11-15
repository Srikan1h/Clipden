# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

home = os.path.expanduser("~")

project_dir = os.path.abspath(SPECPATH + '/..')
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Tcl/Tk data and shared library locations
datas = []
binaries = []

# Tcl data files
if os.path.exists("/usr/share/tcltk/tcl8.6"):
    datas.append(("/usr/share/tcltk/tcl8.6", "tcl8.6"))
elif os.path.exists(f"{home}/.local/usr/share/tcltk/tcl8.6"):
    datas.append((f"{home}/.local/usr/share/tcltk/tcl8.6", "tcl8.6"))

# Tk data files
if os.path.exists("/usr/share/tcltk/tk8.6"):
    datas.append(("/usr/share/tcltk/tk8.6", "tk8.6"))
elif os.path.exists(f"{home}/.local/usr/share/tcltk/tk8.6"):
    datas.append((f"{home}/.local/usr/share/tcltk/tk8.6", "tk8.6"))

# libtk8.6 shared library
libtk_paths = [
    "/usr/lib/x86_64-linux-gnu/libtk8.6.so",
    f"{home}/.local/usr/lib/x86_64-linux-gnu/libtk8.6.so",
]
for p in libtk_paths:
    if os.path.exists(p):
        binaries.append((p, "."))
        break

# Assets (icon)
icon_png = os.path.join(project_dir, "assets", "clipden.png")
icon_svg = os.path.join(project_dir, "assets", "clipden.svg")
if os.path.exists(icon_png):
    datas.append((icon_png, "assets"))
if os.path.exists(icon_svg):
    datas.append((icon_svg, "assets"))

hiddenimports = [
    "clipden",
    "clipden.ui",
    "clipden.ui.app",
    "clipden.ui.styles",
    "clipden.ui.snippet_dialog",
    "clipden.ui.settings_dialog",
    "clipden.database",
    "clipden.clipboard_monitor",
    "clipden.config",
    "clipden.utils",
    "keyring.backends.SecretService",
    "secretstorage",
    "jeepney",
    "pyperclip",
    "supabase",
    "postgrest",
    "realtime",
    "storage3",
    "supabase_auth",
    "supabase_functions",
    "dotenv",
    "tkinter",
    "tkinter.ttk",
    "tkinter.messagebox",
    "tkinter.scrolledtext",
]

runtime_hook_path = os.path.join(project_dir, 'packaging', 'runtime_hook.py')
entry_script = os.path.join(project_dir, 'main.py')

a = Analysis(
    [entry_script],
    pathex=[project_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[runtime_hook_path],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='clipden',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/clipden.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='clipden',
)
