"""Dataset retrieval and private-mirror tooling (honest-scholar#3).

Tier-A git/LFS and Tier-B ``pooch`` fetch need no external binary; private
mirroring shells out to ``rclone`` (an optional single static binary, not a
Python dependency).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def fetch(name: str, dest: str | Path) -> Path:
    """Fetch a registered dataset via pooch, verifying checksums.

    :param name: Registered dataset name.
    :param dest: Destination directory for the fetched files.
    :returns: The path to the fetched dataset root.
    :raises NotImplementedError: Always — pending implementation (honest-scholar#3).
    """
    raise NotImplementedError("dataset retrieval/mirror tooling — see honest-scholar#3")


def mirror(name: str, remote: str) -> None:
    """Mirror a dataset to private storage via rclone.

    :param name: Registered dataset name.
    :param remote: The rclone remote target.
    :raises NotImplementedError: Always — pending implementation (honest-scholar#3).
    """
    raise NotImplementedError("dataset retrieval/mirror tooling — see honest-scholar#3")
