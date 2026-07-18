"""Citation-graph client over external metadata sources (honest-scholar#1)."""

from __future__ import annotations

from typing import Any


def neighbors(identifier: str) -> list[dict[str, Any]]:
    """Return citation-graph neighbors of a work.

    :param identifier: A DOI, arXiv id, or resolved work identifier.
    :returns: A list of neighbor-work metadata mappings.
    :raises NotImplementedError: Always — pending implementation (honest-scholar#1).
    """
    raise NotImplementedError("literature citation-graph client — see honest-scholar#1")
