#!/usr/bin/env bash
# Usage: ./dev.sh "feat: message"
set -e
black src tests && mypy src && pytest -q && git add . \
  && git commit -m "$1" && echo "✅ Tests & commit done."
