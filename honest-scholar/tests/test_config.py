"""Tests for :mod:`honest_scholar.core.config`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from honest_scholar.core import load_config


def test_missing_file_returns_empty(tmp_path: Path) -> None:
    assert load_config(tmp_path / "absent.yml") == {}


def test_reads_mapping(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text(
        "tooling:\n  cli: honest-scholar\n  version: 0.0.0\n", encoding="utf-8"
    )
    config = load_config(path)
    assert config["tooling"]["cli"] == "honest-scholar"


def test_blank_file_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text("", encoding="utf-8")
    assert load_config(path) == {}


def test_non_mapping_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected a YAML mapping"):
        load_config(path)
