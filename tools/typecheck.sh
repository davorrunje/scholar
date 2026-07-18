#!/usr/bin/env bash
set -euo pipefail

# Type-check the honest-scholar package with mypy (strict).
cd "$(dirname "$0")/../honest-scholar"

echo "Running mypy..."
uv run mypy
