#!/usr/bin/env bash
# Ocat Release Script
set -e

echo "🚀 Starting Ocat release process..."

# Test
echo "📋 Running tests..."
poetry run pytest -q

# Format
echo "🎨 Formatting code..."
poetry run black src tests

# Type check
echo "🔍 Type checking..."
poetry run mypy src

# Get current version
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "📦 Current version: $VERSION"

# Build
echo "🔨 Building package..."
poetry build

# Git tag (optional - requires manual version bump first)
read -p "🏷️  Tag and push version v$VERSION? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git tag "v$VERSION"
    git push --tags
    echo "✅ Tagged and pushed v$VERSION"
fi

echo "✅ Release process complete!"
echo "📁 Build artifacts in dist/"
echo "🔖 To bump version: edit pyproject.toml"
