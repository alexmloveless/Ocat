# Release Process

## Quick Release
```bash
./release.sh
```

## Manual Steps
1. **Test**: `poetry run pytest`
2. **Format**: `poetry run black src tests`
3. **Type Check**: `poetry run mypy src`
4. **Version**: Edit `pyproject.toml` version
5. **Build**: `poetry build`
6. **Tag**: `git tag v{version} && git push --tags`

## Files
- `pyproject.toml` - Version and deps
- `src/ocat/` - Main code
- `tests/` - Test suite
- `release.sh` - Automated release script
