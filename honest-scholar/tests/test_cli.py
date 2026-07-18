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


def test_stub_command_exits_2() -> None:
    result = runner.invoke(app, ["dataset", "fetch", "mnist"])
    assert result.exit_code == 2
    assert "not yet implemented" in result.stdout
    assert "honest-scholar#3" in result.stdout


def test_each_group_has_a_stub() -> None:
    cases = [
        (["dataset", "validate", "datasets.yml"], "honest-scholar#2"),
        (["dataset", "emit", "mnist"], "honest-scholar#2"),
        (["dataset", "fetch", "mnist"], "honest-scholar#3"),
        (["dataset", "audit"], "honest-scholar#3"),
        (["defend", "record", "claim"], "honest-scholar#4"),
        (["backlog", "park", "idea"], "honest-scholar#5"),
        (["backlog", "add", "idea"], "honest-scholar#5"),
    ]
    for args, issue in cases:
        result = runner.invoke(app, args)
        assert result.exit_code == 2
        assert "not yet implemented" in result.stdout
        assert issue in result.stdout


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
