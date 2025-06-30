#!/usr/bin/env python3
"""
Entry point for running Ocat as a module.

This allows the package to be executed with:
    python -m ocat [args...]
"""

from .cli import main

if __name__ == "__main__":
    import sys

    sys.exit(main())
