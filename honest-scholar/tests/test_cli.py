"""CLI smoke tests for the ``honest-scholar`` Typer app."""

from __future__ import annotations

from typer.testing import CliRunner

from honest_scholar import __version__
from honest_scholar.cli import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_lists_groups() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for group in ("literature", "dataset", "defend", "backlog"):
        assert group in result.stdout


def test_doctor_runs() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "python" in result.stdout.lower()
    assert "rclone" in result.stdout.lower()
    assert "uv" in result.stdout.lower()


def test_dataset_command_tree_matches_audited_specs() -> None:
    result = runner.invoke(app, ["dataset", "--help"])
    assert result.exit_code == 0
    for command in ("validate", "ingest", "emit", "fetch", "verify", "mirror", "audit"):
        assert command in result.stdout


def test_backlog_command_tree_matches_audited_specs() -> None:
    result = runner.invoke(app, ["backlog", "--help"])
    assert result.exit_code == 0
    for command in ("park", "add", "list", "rank", "promote", "drop"):
        assert command in result.stdout
