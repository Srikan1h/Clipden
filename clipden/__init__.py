"""
ClipDen - Linux Desktop Clipboard Manager
Everything you copy. One place to keep.
"""

import os
import sys
import ctypes

# Ensure ~/.local libraries are discoverable for Tkinter on Ubuntu systems where
# python3-tk is unpacked in user home directory.
_user_home = os.path.expanduser("~")
_user_tk_lib_dir = os.path.join(_user_home, ".local", "usr", "share", "tcltk", "tk8.6")
_user_so_dir = os.path.join(_user_home, ".local", "usr", "lib", "x86_64-linux-gnu")
_user_py_dir = os.path.join(_user_home, ".local", "usr", "lib", "python3.14")
_user_py_dynload = os.path.join(_user_py_dir, "lib-dynload")

if os.path.isdir(_user_tk_lib_dir) and "TK_LIBRARY" not in os.environ:
    os.environ["TK_LIBRARY"] = _user_tk_lib_dir

if os.path.isdir(_user_so_dir):
    libtk_path = os.path.join(_user_so_dir, "libtk8.6.so")
    if os.path.exists(libtk_path):
        try:
            ctypes.CDLL(libtk_path, mode=ctypes.RTLD_GLOBAL)
        except Exception:
            pass

for p in (_user_py_dynload, _user_py_dir):
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

__version__ = "0.1.0"

