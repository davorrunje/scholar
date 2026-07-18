"""End-to-end CLI coverage for the dataset commands + error paths (#16 sweep)."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from honest_scholar.cli import app

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

runner = CliRunner()


def _tier_a_project(tmp_path: Path) -> Path:
    """Create a cwd with a Tier-A datasets.yml + its in-repo file; return cwd."""
    (tmp_path / "data").mkdir()
    payload = b"tier-a bytes"
    (tmp_path / "data" / "f.bin").write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    (tmp_path / "datasets.yml").write_text(
        f"""
datasets:
  - id: ds-a
    version: "1.0.0"
    tier: A
    license: CC0-1.0
    redistributable: true
    access: open
    files:
      - path: data/f.bin
        sha256: {digest}
    datasheet: datasheets/ds-a.md
""",
        encoding="utf-8",
    )
    return tmp_path


def test_validate_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(_tier_a_project(tmp_path))
    result = runner.invoke(app, ["dataset", "validate"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["ok"] is True


def test_validate_malformed_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "datasets.yml").write_text("datasets: [oops\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["dataset", "validate"])
    assert result.exit_code == 1
    assert json.loads(result.stdout)["ok"] is False


def test_ingest_bad_file_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["dataset", "ingest", "nope.json"]).exit_code == 1


def test_emit_all_and_unknown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(_tier_a_project(tmp_path))
    all_ = runner.invoke(app, ["dataset", "emit", "--all"])
    assert all_.exit_code == 0
    assert isinstance(json.loads(all_.stdout), list)
    assert runner.invoke(app, ["dataset", "emit", "ghost"]).exit_code == 1


def test_fetch_and_verify_tier_a(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(_tier_a_project(tmp_path))
    fetch = runner.invoke(app, ["dataset", "fetch", "ds-a"])
    assert fetch.exit_code == 0
    assert json.loads(fetch.stdout) == ["data/f.bin"]
    verify = runner.invoke(app, ["dataset", "verify", "ds-a"])
    assert verify.exit_code == 0
    assert json.loads(verify.stdout)["ok"] is True


def test_fetch_unknown_id_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(_tier_a_project(tmp_path))
    assert runner.invoke(app, ["dataset", "fetch", "ghost"]).exit_code == 1


def test_verify_corrupt_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(_tier_a_project(tmp_path))
    (tmp_path / "data" / "f.bin").write_bytes(b"tampered")
    assert runner.invoke(app, ["dataset", "verify", "ds-a"]).exit_code == 1


def test_mirror_without_config_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(_tier_a_project(tmp_path))
    result = runner.invoke(app, ["dataset", "mirror", "ds-a"])
    assert result.exit_code == 1
    assert "no mirror configured" in result.stderr


def test_audit_whole_and_by_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(_tier_a_project(tmp_path))
    whole = runner.invoke(app, ["dataset", "audit"])
    assert whole.exit_code == 0
    assert json.loads(whole.stdout)["ok"] is True
    by_id = runner.invoke(app, ["dataset", "audit", "ds-a"])
    assert by_id.exit_code == 0


def test_audit_fails_on_missing_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(_tier_a_project(tmp_path))
    (tmp_path / "data" / "f.bin").unlink()
    result = runner.invoke(app, ["dataset", "audit"])
    assert result.exit_code == 1
    assert json.loads(result.stdout)["ok"] is False


def test_emit_no_arg_exits_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(_tier_a_project(tmp_path))
    result = runner.invoke(app, ["dataset", "emit"])
    assert result.exit_code == 1
    assert "give a dataset id or --all" in result.stderr


def test_fetch_tier_c_exits_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "datasets.yml").write_text(
        f"""
datasets:
  - id: ds-c
    version: "1.0.0"
    tier: C
    license: proprietary
    redistributable: false
    access: gated
    files:
      - path: data/c.bin
        sha256: {"d" * 64}
    datasheet: datasheets/ds-c.md
    instructions: email the authors
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["dataset", "fetch", "ds-c"])
    assert result.exit_code == 1
    assert "gated" in result.stderr


def test_mirror_success_with_fake_rclone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from honest_scholar import cli
    from honest_scholar.dataset import retrieval as retrieval_mod

    monkeypatch.chdir(_tier_a_project(tmp_path))

    class _Proc:
        returncode = 0

    def _ok(args: list[str], **_kw: object) -> _Proc:
        return _Proc()

    monkeypatch.setattr(
        cli, "_mirror_from", lambda _m: retrieval_mod.Mirror(remote="store", run=_ok)
    )
    result = runner.invoke(app, ["dataset", "mirror", "ds-a"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["mirrored"] == "ds-a"


def test_emit_malformed_manifest_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "bad.yml").write_text("datasets: [oops\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["dataset", "emit", "x", "--manifest", "bad.yml"])
    assert result.exit_code == 1


def test_fetch_malformed_manifest_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "datasets.yml").write_text("datasets: [oops\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["dataset", "fetch", "x"])
    assert result.exit_code == 1
    assert "manifest error" in result.stderr


def test_mirror_retrieval_error_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "datasets.yml").write_text(
        f"""
mirror:
  rclone_remote: store
  base_path: base
datasets:
  - id: ds-c
    version: "1.0.0"
    tier: C
    license: proprietary
    redistributable: false
    access: gated
    files:
      - path: data/c.bin
        sha256: {"d" * 64}
    datasheet: datasheets/ds-c.md
    instructions: email the authors
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["dataset", "mirror", "ds-c"])
    assert result.exit_code == 1
    assert "mirror failed" in result.stderr
