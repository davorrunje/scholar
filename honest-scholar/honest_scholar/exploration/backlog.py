"""Exploration backlog helper (honest-scholar#5)."""

from __future__ import annotations

from typing import Any


def add(item: str) -> dict[str, Any]:
    """Add an item to the exploration backlog.

    :param item: The backlog item description.
    :returns: The created backlog entry.
    :raises NotImplementedError: Always — pending implementation (honest-scholar#5).
    """
    raise NotImplementedError("exploration backlog helper — see honest-scholar#5")


def rank() -> list[dict[str, Any]]:
    """Rank the exploration backlog by priority.

    :returns: The backlog entries in ranked order.
    :raises NotImplementedError: Always — pending implementation (honest-scholar#5).
    """
    raise NotImplementedError("exploration backlog helper — see honest-scholar#5")
