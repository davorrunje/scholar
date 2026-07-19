#!/usr/bin/env bash
set -euo pipefail

# Validate the Claude Code plugin manifest.
# Prefer the official `claude plugin validate` when the CLI is on PATH;
# otherwise fall back to a structural check (JSON well-formedness + required
# keys), so a schema-invalid manifest does not pass CI just for parsing.
cd "$(dirname "$0")/.."

if command -v claude >/dev/null 2>&1; then
    echo "Validating plugin via 'claude plugin validate .'..."
    claude plugin validate .
else
    echo "'claude' not on PATH — falling back to a structural manifest check..."
    python3 - <<'PY'
import json
import sys

errors = []


def require(cond, msg):
    if not cond:
        errors.append(msg)


with open(".claude-plugin/plugin.json", encoding="utf-8") as fh:
    plugin = json.load(fh)
require(isinstance(plugin, dict), "plugin.json: must be a JSON object")
for key in ("name", "version", "description"):
    require(bool(plugin.get(key)), f"plugin.json: missing/empty required key '{key}'")

with open(".claude-plugin/marketplace.json", encoding="utf-8") as fh:
    market = json.load(fh)
require(isinstance(market, dict), "marketplace.json: must be a JSON object")
require(bool(market.get("name")), "marketplace.json: missing/empty 'name'")
plugins = market.get("plugins")
require(
    isinstance(plugins, list) and len(plugins) >= 1,
    "marketplace.json: 'plugins' must be a non-empty list",
)
for i, entry in enumerate(plugins or []):
    require(
        isinstance(entry, dict) and entry.get("name"),
        f"marketplace.json: plugins[{i}] missing 'name'",
    )
    require(
        isinstance(entry, dict) and entry.get("source") is not None,
        f"marketplace.json: plugins[{i}] missing 'source'",
    )

if errors:
    print("plugin manifest validation FAILED:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)
print("plugin manifests are structurally valid (JSON + required keys)")
PY
fi
