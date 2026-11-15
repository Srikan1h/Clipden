"""
ClipDen application main entry point.
"""

import sys
import tkinter as tk
import clipden
from clipden.ui.app import ClipDenApp


def main():
    if "--version" in sys.argv:
        print(f"ClipDen v{clipden.__version__}")
        sys.exit(0)

    root = tk.Tk()
    app = ClipDenApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
