"""
Runtime hook for PyInstaller bundle.
Sets up TCL_LIBRARY and TK_LIBRARY environment variables from the bundled directory.
"""
import os
import sys

base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# Point Tcl/Tk to bundled directories if present
bundled_tcl = os.path.join(base_dir, 'tcl8.6')
bundled_tk = os.path.join(base_dir, 'tk8.6')

if os.path.isdir(bundled_tcl):
    os.environ['TCL_LIBRARY'] = bundled_tcl
elif os.path.isdir('/usr/share/tcltk/tcl8.6'):
    os.environ['TCL_LIBRARY'] = '/usr/share/tcltk/tcl8.6'

if os.path.isdir(bundled_tk):
    os.environ['TK_LIBRARY'] = bundled_tk
elif os.path.isdir('/usr/share/tcltk/tk8.6'):
    os.environ['TK_LIBRARY'] = '/usr/share/tcltk/tk8.6'
