"""Tests for the shared exploration-backlog helper (honest-scholar#5)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from honest_scholar.cli import app
from honest_scholar.exploration import backlog as b

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


def test_round_trip_preserves_rows() -> None:
    board = b.Backlog(level="hypothesis")
    board.add("X does Y under Z", "scouted:W123")
    board.park("a hunch", "own")
    reloaded = b.Backlog.loads(board.dumps(), "hypothesis")
    assert [r["one-line"] for r in reloaded.rows] == ["X does Y under Z", "a hunch"]
    assert reloaded.rows[0]["status"] == "candidate"
    assert reloaded.rows[1]["status"] == "parked"


def test_pipe_in_provenance_survives_round_trip() -> None:
    board = b.Backlog(level="hypothesis")
    snippet = "unlike [anchor] | our method needs no lattice"
    board.add("a claim", snippet)
    reloaded = b.Backlog.loads(board.dumps(), "hypothesis")
    assert reloaded.rows[0]["provenance"] == snippet


def test_park_and_add_require_provenance() -> None:
    board = b.Backlog(level="hypothesis")
    with pytest.raises(b.BacklogError, match="provenance is required"):
        board.park("idea", "  ")
    with pytest.raises(b.BacklogError, match="provenance is required"):
        board.add("idea", "")


def test_rank_only_from_candidate_or_parked() -> None:
    board = b.Backlog(level="hypothesis")
    row = board.add("claim", "own")
    board.rank(row["id"], EIG="high", feas="med", interest="high")
    assert board.get(row["id"])["status"] == "ranked"
    assert board.get(row["id"])["EIG"] == "high"
    # Ranking an already-ranked row is illegal.
    with pytest.raises(b.BacklogError, match="cannot rank"):
        board.rank(row["id"])


def test_promote_only_from_ranked() -> None:
    board = b.Backlog(level="hypothesis")
    row = board.add("claim", "own")
    with pytest.raises(b.BacklogError, match="cannot promote"):
        board.promote(row["id"])
    board.rank(row["id"])
    board.promote(row["id"])
    assert board.get(row["id"])["status"] == "promoted"


def test_drop_requires_reason_and_keeps_row() -> None:
    board = b.Backlog(level="hypothesis")
    row = board.add("claim", "own")
    with pytest.raises(b.BacklogError, match="drop reason is required"):
        board.drop(row["id"], "")
    board.drop(row["id"], "superseded by newer idea")
    kept = board.get(row["id"])
    assert kept["status"] == "dropped"
    assert kept["note"] == "superseded by newer idea"


def test_unknown_id_raises() -> None:
    board = b.Backlog(level="hypothesis")
    with pytest.raises(b.BacklogError, match="no backlog row"):
        board.get("nope")


def test_fresh_ids_are_unique() -> None:
    board = b.Backlog(level="hypothesis")
    a = board.add("same title", "own")
    c = board.add("same title", "own")
    assert a["id"] != c["id"]


def test_paper_level_uses_lens_columns() -> None:
    board = b.Backlog(level="paper")
    assert "lens" in board.columns
    assert "EIG" not in board.columns


def test_scaffold_hypothesis_writes_frontmatter(tmp_path: Path) -> None:
    target = b.scaffold_hypothesis(
        tmp_path / "paperA",
        "2026-07-18-monotone-depth",
        "deep nets beat shallow",
        'scouted:W1 "snippet"',
        today="2026-07-18",
    )
    text = target.read_text(encoding="utf-8")
    assert target.name == "hypothesis.md"
    assert "level: hypothesis" in text
    assert "id: 2026-07-18-monotone-depth" in text
    assert "last-updated: 2026-07-18" in text
    assert 'scouted:W1 "snippet"' in text
    # Refuses to overwrite.
    with pytest.raises(b.BacklogError, match="already exists"):
        b.scaffold_hypothesis(
            tmp_path / "paperA", "2026-07-18-monotone-depth", "x", "own"
        )


def test_scaffold_paper_creates_root_and_registers(tmp_path: Path) -> None:
    research = tmp_path / "docs" / "research"
    research.mkdir(parents=True)
    root = b.scaffold_paper(
        research, "depth-collapse", "a follow-up paper", backend="bench"
    )
    assert (root / "paper" / "pitch.md").is_file()
    assert (root / "backlog.md").is_file()
    registry = (research / "papers.md").read_text(encoding="utf-8")
    assert "depth-collapse" in registry
    assert "bench" in registry
    with pytest.raises(b.BacklogError, match="already"):
        b.scaffold_paper(research, "depth-collapse", "dup")


def test_append_papers_registry_rejects_duplicate(tmp_path: Path) -> None:
    papers = tmp_path / "papers.md"
    b.append_papers_registry(papers, "p1", "docs/research/p1", "bench")
    with pytest.raises(b.BacklogError, match="already"):
        b.append_papers_registry(papers, "p1", "docs/research/p1", "bench")


# --- CLI ---------------------------------------------------------------------


def test_cli_park_then_list(tmp_path: Path) -> None:
    path = tmp_path / "backlog.md"
    result = runner.invoke(
        app,
        ["backlog", "park", "an idea", "--provenance", "own", "--backlog", str(path)],
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout)["status"] == "parked"

    listed = runner.invoke(app, ["backlog", "list", "--backlog", str(path)])
    assert listed.exit_code == 0
    assert len(json.loads(listed.stdout)) == 1


def test_cli_park_without_provenance_fails(tmp_path: Path) -> None:
    path = tmp_path / "backlog.md"
    result = runner.invoke(
        app, ["backlog", "park", "idea", "--provenance", "", "--backlog", str(path)]
    )
    assert result.exit_code == 1


def test_cli_bad_level_exits_2(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["backlog", "list", "--backlog", str(tmp_path / "b.md"), "--level", "galaxy"],
    )
    assert result.exit_code == 2


def test_cli_full_lifecycle(tmp_path: Path) -> None:
    path = str(tmp_path / "backlog.md")
    added = runner.invoke(
        app,
        [
            "backlog",
            "add",
            "claim",
            "--provenance",
            "own",
            "--backlog",
            path,
            "--id",
            "h1",
        ],
    )
    assert added.exit_code == 0
    ranked = runner.invoke(
        app, ["backlog", "rank", "h1", "--backlog", path, "--feas", "high"]
    )
    assert json.loads(ranked.stdout)["status"] == "ranked"
    promoted = runner.invoke(app, ["backlog", "promote", "h1", "--backlog", path])
    assert json.loads(promoted.stdout)["status"] == "promoted"
