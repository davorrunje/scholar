"""Thin dataset-manifest tooling (honest-scholar#2)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


def register(name: str, source: str) -> dict[str, Any]:
    """Register a dataset in the thin manifest.

    :param name: Human-readable dataset name.
    :param source: The dataset source (URL, DOI, or git/LFS locator).
    :returns: The manifest entry created for the dataset.
    :raises NotImplementedError: Always — pending implementation (honest-scholar#2).
    """
    raise NotImplementedError("dataset manifest tooling — see honest-scholar#2")


def audit(manifest_path: str | Path) -> dict[str, Any]:
    """Audit a dataset manifest's provenance and mirror state.

    :param manifest_path: Path to the manifest file to audit.
    :returns: An audit report mapping.
    :raises NotImplementedError: Always — pending implementation (honest-scholar#2).
    """
    raise NotImplementedError("dataset manifest tooling — see honest-scholar#2")
