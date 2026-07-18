"""honest-scholar — supporting CLI/tooling for the honest-scholar research plugin.

The authoritative interface is the ``honest-scholar`` Typer CLI
(:mod:`honest_scholar.cli`); an optional MCP wrapper over the same modules may
follow later (see ADR-0024).
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("honest-scholar")
except PackageNotFoundError:  # pragma: no cover - not installed (e.g. source tree)
    __version__ = "0.0.0"

__all__ = ["__version__"]
