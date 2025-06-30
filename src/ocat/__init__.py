"""
Ocat - An interactive LLM Chat CLI tool.

A command-line interface for interacting with Large Language Models
through an intuitive and user-friendly terminal interface.
"""

# Disable ChromaDB telemetry globally before any imports
import os
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

__version__ = "0.1.0"
__author__ = "Alex Loveless"
__email__ = "alex@alexloveless.uk"

from .cli import main

__all__ = ["main"]
