#!/usr/bin/env python3
"""
Main launcher script for ClipDen.
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clipden.__main__ import main

if __name__ == "__main__":
    main()

