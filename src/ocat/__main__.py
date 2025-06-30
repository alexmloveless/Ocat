#!/usr/bin/env python3
"""
Entry point for running Ocat as a module.

This allows the package to be executed with:
    python -m ocat [args...]
"""

# Disable ChromaDB telemetry globally before any imports
import os

os.environ["ANONYMIZED_TELEMETRY"] = "False"
# Disable tokenizers parallelism to prevent fork warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from .cli import main

if __name__ == "__main__":
    import sys

    sys.exit(main())
