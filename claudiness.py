#!/usr/bin/env python3
"""
Claudiness Score - Legacy backward-compatibility wrapper.

This file preserves the original `python claudiness.py` interface.
The implementation has moved to the `claudiness` package (src/claudiness/).

For the full multi-model CLI, install the package:
    pip install -e .
    claudiness --help
"""

import sys
import os

# Add src/ to path so the package can be imported without installing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from claudiness.cli import main

if __name__ == '__main__':
    main()
