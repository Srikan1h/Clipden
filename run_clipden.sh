#!/usr/bin/env bash
# ClipDen Launcher Script for Ubuntu Linux (Wayland / X11)

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Set up local paths if unpacked in ~/.local
export TK_LIBRARY="${TK_LIBRARY:-$HOME/.local/usr/share/tcltk/tk8.6}"
export LD_LIBRARY_PATH="$HOME/.local/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export PYTHONPATH="$DIR:$HOME/.local/usr/lib/python3.14/lib-dynload:$HOME/.local/usr/lib/python3.14:$PYTHONPATH"

# Run with virtual environment if present
if [ -f "$DIR/.venv/bin/python" ]; then
    exec "$DIR/.venv/bin/python" "$DIR/main.py" "$@"
else
    exec python3 "$DIR/main.py" "$@"
fi
