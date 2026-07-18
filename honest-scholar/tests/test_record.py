"""Tests for the ``defend record`` helper (honest-scholar#4)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
import yaml
from typer.testing import CliRunner

from honest_scholar.cli import app
from honest_scholar.defend import record as r

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()

_ARTIFACT = """\
---
status:
  level: hypothesis
  id: 2026-07-18-x
  verdict: pending
  understanding: {status: pending, unresolved: []}   # written by the defend skill
  last-updated: 2026-01-01
---

# Hypothesis: x

Body stays intact.
"""


def _artifact(tmp_path: Path) -> Path:
    path = tmp_path / "findings.md"
    path.write_text(_ARTIFACT, encoding="utf-8")
    return path


def test_patch_sets_understanding_and_preserves_rest() -> None:
    out = r.patch_understanding(_ARTIFACT, "ok", [], last_updated="2026-07-18")
    parsed = yaml.safe_load(out.split("---")[1])
    assert parsed["status"]["understanding"] == {"status": "ok", "unresolved": []}
    assert str(parsed["status"]["last-updated"]) == "2026-07-18"
    # Body and unrelated frontmatter untouched.
    assert "Body stays intact." in out
    assert "verdict: pending" in out
    assert "# written by the defend skill" in out  # comment preserved


def test_patch_records_gaps() -> None:
    out = r.patch_understanding(
        _ARTIFACT,
        "gaps",
        ["no answer to the falsification probe"],
        last_updated="2026-07-18",
    )
    parsed = yaml.safe_load(out.split("---")[1])
    assert parsed["status"]["understanding"]["status"] == "gaps"
    assert parsed["status"]["understanding"]["unresolved"] == [
        "no answer to the falsification probe"
    ]


def test_patch_inserts_missing_fields() -> None:
    minimal = "---\nstatus:\n  level: hypothesis\n---\n\n# body\n"
    out = r.patch_understanding(minimal, "ok", [], last_updated="2026-07-18")
    parsed = yaml.safe_load(out.split("---")[1])
    assert parsed["status"]["understanding"] == {"status": "ok", "unresolved": []}
    assert str(parsed["status"]["last-updated"]) == "2026-07-18"


def test_patch_rejects_bad_status() -> None:
    with pytest.raises(r.RecordError, match="status must be"):
        r.patch_understanding(_ARTIFACT, "great", [], last_updated="2026-07-18")


def test_patch_requires_frontmatter() -> None:
    with pytest.raises(r.RecordError, match="no YAML frontmatter"):
        r.patch_understanding("# no frontmatter\n", "ok", [], last_updated="x")


def test_patch_is_idempotent() -> None:
    once = r.patch_understanding(_ARTIFACT, "ok", [], last_updated="2026-07-18")
    twice = r.patch_understanding(once, "ok", [], last_updated="2026-07-18")
    assert once == twice


def test_record_ok_writes_log(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    result = r.record(
        artifact,
        "methodology",
        [],
        log_dir=tmp_path / "log",
        today="2026-07-18",
    )
    assert result.outcome == "resolved"
    assert result.log_entry.is_file()
    entry = yaml.safe_load(result.log_entry.read_text(encoding="utf-8"))[0]
    assert entry["target"] == "methodology"
    assert entry["status"] == "ok"


def test_record_bad_target_raises(tmp_path: Path) -> None:
    with pytest.raises(r.RecordError, match="target must be"):
        r.record(_artifact(tmp_path), "vibes", [], today="2026-07-18")


def test_record_gaps_passed_requires_sign_off(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    with pytest.raises(r.RecordError, match="requires a named"):
        r.record(
            artifact, "claim", ["unanswered probe"], override=True, today="2026-07-18"
        )


def test_record_override_with_sign_off(tmp_path: Path) -> None:
    result = r.record(
        _artifact(tmp_path),
        "claim",
        ["unanswered probe"],
        override=True,
        signed_off_by="D. Runje",
        log_dir=tmp_path / "log",
        today="2026-07-18",
    )
    assert result.outcome == "overridden"


def test_record_per_gap_acknowledgement(tmp_path: Path) -> None:
    result = r.record(
        _artifact(tmp_path),
        "claim",
        ["gap one"],
        acknowledgements=[{"gap": "gap one", "by": "D. Runje"}],
        signed_off_by="D. Runje",
        log_dir=tmp_path / "log",
        today="2026-07-18",
    )
    assert result.outcome == "acknowledged-per-gap"


def test_record_writes_transcript(tmp_path: Path) -> None:
    result = r.record(
        _artifact(tmp_path),
        "methodology",
        [],
        transcript="Q: why TOST? A: ...",
        log_dir=tmp_path / "log",
        today="2026-07-18",
    )
    assert result.transcript is not None
    assert result.transcript.read_text(encoding="utf-8").startswith("Q: why TOST?")


def test_record_never_writes_a_verdict_field(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    r.record(artifact, "claim", [], log_dir=tmp_path / "log", today="2026-07-18")
    parsed = yaml.safe_load(artifact.read_text(encoding="utf-8").split("---")[1])
    # The verdict the artifact already had is untouched; record never sets it.
    assert parsed["status"]["verdict"] == "pending"


# --- CLI ---------------------------------------------------------------------


def test_cli_record(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    result = runner.invoke(
        app,
        [
            "defend",
            "record",
            "--artifact",
            str(artifact),
            "--target",
            "methodology",
            "--log-dir",
            str(tmp_path / "log"),
        ],
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout)["outcome"] == "resolved"


def test_cli_record_gaps_without_sign_off_fails(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    result = runner.invoke(
        app,
        [
            "defend",
            "record",
            "--artifact",
            str(artifact),
            "--target",
            "claim",
            "--gaps",
            "unanswered probe",
            "--override",
            "--log-dir",
            str(tmp_path / "log"),
        ],
    )
    assert result.exit_code == 1
