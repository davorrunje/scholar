"""Tests for the CLI-owned API-key store and the ``keys`` command group (#42).

Deterministic throughout: the store path is a ``tmp_path`` (module tests) or the
CLI's cwd via ``monkeypatch.chdir``; the environment is driven with
``monkeypatch``; stdin is fed via ``CliRunner(input=...)``. No test ever asserts a
secret *value* appears in output — only presence/absence and source.
"""

from __future__ import annotations

import json
import stat
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from honest_scholar import cli
from honest_scholar.cli import app
from honest_scholar.core import keys as keys_mod

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


# --- registry ---------------------------------------------------------------


def test_is_known_registry_rclone_and_unknown() -> None:
    assert keys_mod.is_known("S2_API_KEY") is True
    assert keys_mod.is_known("RCLONE_CONFIG_STORE_TYPE") is True
    assert keys_mod.is_known("MYSTERY") is False


# --- store round-trip + permissions -----------------------------------------


def test_store_path_default_and_override(tmp_path: Path) -> None:
    assert keys_mod.store_path() == keys_mod.STORE_PATH
    override = tmp_path / "k.json"
    assert keys_mod.store_path(override) == override


def test_missing_store_is_empty(tmp_path: Path) -> None:
    assert keys_mod.load_store(tmp_path / "absent.json") == {}


def test_set_creates_parent_and_0600(tmp_path: Path) -> None:
    store = tmp_path / "nested" / "keys.json"
    keys_mod.set_key("S2_API_KEY", "secret", store)
    assert keys_mod.load_store(store) == {"S2_API_KEY": "secret"}
    assert stat.S_IMODE(store.stat().st_mode) == 0o600


def test_load_store_rejects_bad_json(tmp_path: Path) -> None:
    store = tmp_path / "keys.json"
    store.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        keys_mod.load_store(store)


def test_load_store_rejects_non_object(tmp_path: Path) -> None:
    store = tmp_path / "keys.json"
    store.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="expected a JSON object"):
        keys_mod.load_store(store)


def test_load_store_rejects_non_string_value(tmp_path: Path) -> None:
    store = tmp_path / "keys.json"
    store.write_text('{"S2_API_KEY": 5}', encoding="utf-8")
    with pytest.raises(ValueError, match="must be a string"):
        keys_mod.load_store(store)


def test_unset_present_and_absent(tmp_path: Path) -> None:
    store = tmp_path / "keys.json"
    keys_mod.set_key("S2_API_KEY", "secret", store)
    assert keys_mod.unset_key("S2_API_KEY", store) is True
    assert keys_mod.load_store(store) == {}
    assert keys_mod.unset_key("S2_API_KEY", store) is False


# --- precedence: os.environ > store > None ----------------------------------


def test_get_precedence(tmp_path: Path) -> None:
    store = tmp_path / "keys.json"
    keys_mod.set_key("S2_API_KEY", "from-store", store)
    # store wins over unset environment
    assert keys_mod.get("S2_API_KEY", path=store, environ={}) == "from-store"
    # a present env var always wins
    assert (
        keys_mod.get("S2_API_KEY", path=store, environ={"S2_API_KEY": "from-env"})
        == "from-env"
    )
    # unset everywhere
    assert keys_mod.get("OPENALEX_MAILTO", path=store, environ={}) is None


def test_get_defaults_to_os_environ(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)  # default store path is absent under a fresh cwd
    monkeypatch.setenv("S2_API_KEY", "env-default")
    assert keys_mod.get("S2_API_KEY") == "env-default"


def test_source_of(tmp_path: Path) -> None:
    store = tmp_path / "keys.json"
    keys_mod.set_key("S2_API_KEY", "s", store)
    assert keys_mod.source_of("S2_API_KEY", path=store, environ={}) == "store"
    assert (
        keys_mod.source_of("S2_API_KEY", path=store, environ={"S2_API_KEY": "e"})
        == "env"
    )
    assert keys_mod.source_of("OPENALEX_MAILTO", path=store, environ={}) is None


# --- scoped env (least privilege) -------------------------------------------


def test_scoped_env_only_present_requested(tmp_path: Path) -> None:
    store = tmp_path / "keys.json"
    keys_mod.set_key("S2_API_KEY", "s", store)
    keys_mod.set_key("OPENALEX_MAILTO", "m", store)
    scoped = keys_mod.scoped_env(
        ["S2_API_KEY", "OPENALEX_MAILTO", "MISSING"], path=store, environ={}
    )
    assert scoped == {"S2_API_KEY": "s", "OPENALEX_MAILTO": "m"}
    assert "MISSING" not in scoped


def test_rclone_config_env_translation() -> None:
    env = keys_mod.rclone_config_env("myremote", {"type": "s3", "access_key_id": "AK"})
    assert env == {
        "RCLONE_CONFIG_MYREMOTE_TYPE": "s3",
        "RCLONE_CONFIG_MYREMOTE_ACCESS_KEY_ID": "AK",
    }


def test_rclone_scoped_env_is_per_remote(tmp_path: Path) -> None:
    store = tmp_path / "keys.json"
    keys_mod.set_key("RCLONE_CONFIG_STORE_TYPE", "s3", store)
    keys_mod.set_key("RCLONE_CONFIG_STORE_SECRET_ACCESS_KEY", "shh", store)
    keys_mod.set_key("RCLONE_CONFIG_OTHER_TYPE", "sftp", store)
    scoped = keys_mod.rclone_scoped_env("store", path=store, environ={})
    assert scoped == {
        "RCLONE_CONFIG_STORE_TYPE": "s3",
        "RCLONE_CONFIG_STORE_SECRET_ACCESS_KEY": "shh",
    }
    # a var supplied only via the environment is picked up too
    scoped_env_only = keys_mod.rclone_scoped_env(
        "store", path=store, environ={"RCLONE_CONFIG_STORE_TOKEN": "t"}
    )
    assert scoped_env_only["RCLONE_CONFIG_STORE_TOKEN"] == "t"


# --- keys CLI group ---------------------------------------------------------


def test_set_single_via_stdin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["keys", "set", "S2_API_KEY"], input="s3cr3t\n")
    assert result.exit_code == 0
    assert "s3cr3t" not in result.stdout  # never echoes the value
    assert keys_mod.load_store() == {"S2_API_KEY": "s3cr3t"}


def test_set_numeric_value_is_not_treated_as_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # "12345" is valid JSON but not an object → stored as a single value.
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["keys", "set", "S2_API_KEY"], input="12345")
    assert result.exit_code == 0
    assert keys_mod.load_store() == {"S2_API_KEY": "12345"}


def test_set_json_blob_sets_many(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    blob = json.dumps({"S2_API_KEY": "a", "OPENALEX_MAILTO": "me@x.org"})
    result = runner.invoke(app, ["keys", "set"], input=blob)
    assert result.exit_code == 0
    assert "a" not in result.stdout.split()  # no value echoed
    assert keys_mod.load_store() == {"S2_API_KEY": "a", "OPENALEX_MAILTO": "me@x.org"}


def test_set_json_blob_empty_object_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["keys", "set"], input="{}")
    assert result.exit_code == 2
    assert "empty" in result.stderr


def test_set_json_blob_non_string_value_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["keys", "set"], input='{"S2_API_KEY": 5}')
    assert result.exit_code == 2
    assert "must be a string" in result.stderr


def test_set_unknown_name_warns_but_stores(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["keys", "set", "MYSTERY_KEY"], input="v\n")
    assert result.exit_code == 0
    assert "not a known key" in result.stderr
    assert keys_mod.load_store() == {"MYSTERY_KEY": "v"}


def test_set_missing_name_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    # A bare token (not a JSON object) piped with no NAME argument.
    result = runner.invoke(app, ["keys", "set"], input="loose-token\n")
    assert result.exit_code == 2
    assert "provide NAME" in result.stderr


def test_set_empty_value_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["keys", "set", "S2_API_KEY"], input="   \n")
    assert result.exit_code == 2
    assert "empty value" in result.stderr


def test_set_interactive_uses_hidden_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_stdin_is_piped", lambda: False)
    monkeypatch.setattr(
        "honest_scholar.cli.getpass.getpass", lambda prompt: "typed-secret"
    )
    result = runner.invoke(app, ["keys", "set", "S2_API_KEY"])
    assert result.exit_code == 0
    assert "typed-secret" not in result.stdout
    assert keys_mod.load_store() == {"S2_API_KEY": "typed-secret"}


def test_set_interactive_missing_name_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_stdin_is_piped", lambda: False)

    def _never(prompt: str) -> str:  # pragma: no cover - must not be called
        raise AssertionError("getpass must not run without a name")

    monkeypatch.setattr("honest_scholar.cli.getpass.getpass", _never)
    result = runner.invoke(app, ["keys", "set"])
    assert result.exit_code == 2
    assert "provide NAME" in result.stderr


def test_list_reports_presence_and_source_not_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    keys_mod.set_key("S2_API_KEY", "topsecret")
    keys_mod.set_key("RCLONE_CONFIG_STORE_TOKEN", "mirror-cred")
    result = runner.invoke(app, ["keys", "list"])
    assert result.exit_code == 0
    assert "topsecret" not in result.stdout
    assert "mirror-cred" not in result.stdout
    rows = {row["name"]: row for row in json.loads(result.stdout)}
    assert rows["S2_API_KEY"]["present"] is True
    assert rows["S2_API_KEY"]["source"] == "store"
    assert "how_to_obtain" in rows["S2_API_KEY"]
    # an unset known key is reported absent
    assert rows["OPENALEX_MAILTO"]["present"] is False
    assert rows["OPENALEX_MAILTO"]["source"] is None
    # the stored rclone credential shows up as an extra, metadata-less row
    assert rows["RCLONE_CONFIG_STORE_TOKEN"]["present"] is True
    assert rows["RCLONE_CONFIG_STORE_TOKEN"]["service"] is None


def test_check_env_source_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    keys_mod.set_key("S2_API_KEY", "from-store")
    monkeypatch.setenv("S2_API_KEY", "from-env")
    result = runner.invoke(app, ["keys", "check"])
    assert result.exit_code == 0
    assert "from-store" not in result.stdout
    assert "from-env" not in result.stdout
    rows = {row["name"]: row for row in json.loads(result.stdout)}
    assert rows["S2_API_KEY"] == {
        "name": "S2_API_KEY",
        "present": True,
        "source": "env",
    }


def test_unset_present_then_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    keys_mod.set_key("S2_API_KEY", "s")
    ok = runner.invoke(app, ["keys", "unset", "S2_API_KEY"])
    assert ok.exit_code == 0
    assert "unset S2_API_KEY" in ok.stdout
    again = runner.invoke(app, ["keys", "unset", "S2_API_KEY"])
    assert again.exit_code == 0
    assert "was not in the store" in again.stderr


def test_path_prints_store_path() -> None:
    result = runner.invoke(app, ["keys", "path"])
    assert result.exit_code == 0
    assert result.stdout.strip() == str(keys_mod.STORE_PATH)


# --- integration: doctor + _lit_client --------------------------------------


def test_doctor_reports_key_presence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    keys_mod.set_key("S2_API_KEY", "s")
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "S2_API_KEY: set (source: store)" in result.stdout
    assert "OPENALEX_MAILTO: not set" in result.stdout


def test_lit_client_sources_s2_key_from_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("S2_API_KEY", raising=False)
    keys_mod.set_key("S2_API_KEY", "store-key")
    client = cli._lit_client()
    assert client.s2_key == "store-key"
