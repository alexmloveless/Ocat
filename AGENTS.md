# Agent Guide for Ocat

Always use the ocat conda environment for any work on this repo.

Quickstart:

- Activate: `conda activate ocat`
- Install/refresh deps: `uv pip install -e .` (installs runtime deps) and `uv pip install pytest black mypy ruff types-PyYAML pytest-asyncio` (dev tools)
- Run tests: `pytest`
- Format: `black .`
- Type check: `mypy .`

Notes:
- Python: 3.12 (conda env manages this)
- If the environment is missing, create it: `conda create -y -n ocat python=3.12` then activate and run the install commands above.
- Prefer uv for Python package installs.
