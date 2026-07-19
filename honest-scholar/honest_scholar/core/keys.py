"""CLI-owned API-key store (ADR-0029).

A single, controlled place to store, read and check the service keys the tooling
uses — Semantic Scholar (``S2_API_KEY``), the OpenAlex polite pool
(``OPENALEX_MAILTO``) and private rclone-mirror credentials — without leaking a
secret through shell history, ``argv`` or an over-broad always-present file.

Design (ADR-0029):

- **Store.** A JSON object ``{name: value}`` at ``.honest-scholar/keys.json`` —
  gitignored, created ``0600``. JSON (not ``.env``) because the CLI is the sole
  reader/writer. Per-key *metadata* (service, how-to-obtain link, rate-limit
  benefit) lives in the :data:`KNOWN_KEYS` registry — the single source of truth —
  rather than being duplicated into every stored record.
- **Precedence.** :func:`get` resolves ``os.environ`` **>** the store **>**
  ``None``, so an injected environment variable always wins (CI / secrets
  injection) and the service degrades gracefully when a key is unset.
- **Least privilege.** :func:`scoped_env` / :func:`rclone_scoped_env` build an
  in-memory ``env`` dict holding *only* the secrets a given child process needs —
  never the whole store, never a file on the default path.
- **Honesty.** The store is **plaintext at rest**. ``gitignore`` + ``0600`` limit
  exposure but are *not* encryption; OS-keychain backing is the follow-up (#49).
  Nothing in this module logs or echoes a value.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

#: The CLI-owned store path (relative to the project root / current directory).
STORE_PATH = Path(".honest-scholar/keys.json")

#: Prefix for rclone remote-config credentials handed to the rclone subprocess as
#: ``RCLONE_CONFIG_<REMOTE>_<PARAM>`` environment variables (no config file).
RCLONE_ENV_PREFIX = "RCLONE_CONFIG_"


@dataclass(frozen=True)
class KnownKey:
    """A documented, recognised key the tooling knows how to use.

    :param name: The environment-variable / store name (e.g. ``S2_API_KEY``).
    :param service: The service the key authenticates or identifies to.
    :param benefit: What providing it buys (a rate-limit / politeness benefit).
    :param how_to_obtain: A URL describing how to obtain the key.
    """

    name: str
    service: str
    benefit: str
    how_to_obtain: str


#: The recognised-keys registry — the single source of truth for key metadata.
KNOWN_KEYS: dict[str, KnownKey] = {
    "S2_API_KEY": KnownKey(
        name="S2_API_KEY",
        service="Semantic Scholar",
        benefit=(
            "Raises the Semantic Scholar rate limit well above the shared keyless "
            "pool, which throttles hard and stalls citation-graph lookups."
        ),
        how_to_obtain="https://www.semanticscholar.org/product/api#api-key",
    ),
    "OPENALEX_MAILTO": KnownKey(
        name="OPENALEX_MAILTO",
        service="OpenAlex",
        benefit=(
            "Joins the OpenAlex 'polite pool' (a contact email), giving faster, "
            "more reliable responses than the anonymous pool."
        ),
        how_to_obtain="https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication",
    ),
}


def is_known(name: str) -> bool:
    """Return whether `name` is a recognised key.

    Recognised means either a registry entry or an rclone remote-config variable
    (``RCLONE_CONFIG_<REMOTE>_<PARAM>``), which are accepted by convention.

    :param name: The candidate key name.
    :returns: ``True`` if the name is documented or an rclone-config variable.
    """
    return name in KNOWN_KEYS or name.startswith(RCLONE_ENV_PREFIX)


def store_path(path: str | Path | None = None) -> Path:
    """Resolve the store path, defaulting to :data:`STORE_PATH`.

    :param path: An explicit override; ``None`` uses the default store path.
    :returns: The path the store is read from / written to.
    """
    return Path(path) if path is not None else STORE_PATH


def load_store(path: str | Path | None = None) -> dict[str, str]:
    """Load the key store as a ``{name: value}`` mapping.

    A missing store yields an empty mapping rather than an error, so callers can
    treat an unconfigured project as "no stored keys".

    :param path: Store path override; defaults to :data:`STORE_PATH`.
    :returns: The stored ``{name: value}`` pairs (empty if the file is absent).
    :raises ValueError: If the file exists but is not a JSON object of strings.
    """
    resolved = store_path(path)
    if not resolved.is_file():
        return {}
    try:
        data = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        msg = f"{resolved}: invalid JSON: {exc}"
        raise ValueError(msg) from exc
    if not isinstance(data, dict):
        msg = f"{resolved}: expected a JSON object, got {type(data).__name__}"
        raise ValueError(msg)
    result: dict[str, str] = {}
    for name, value in data.items():
        if not isinstance(value, str):
            msg = f"{resolved}: value for {name!r} must be a string"
            raise ValueError(msg)
        result[str(name)] = value
    return result


def write_store(mapping: Mapping[str, str], path: str | Path | None = None) -> None:
    """Write `mapping` to the store, creating it ``0600``.

    The parent directory is created if needed; the file mode is tightened to
    owner-read/write only. Values are written verbatim (plaintext at rest — this
    is not encryption; see the module docstring).

    :param mapping: The ``{name: value}`` pairs to persist.
    :param path: Store path override; defaults to :data:`STORE_PATH`.
    """
    resolved = store_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dict(sorted(mapping.items())), indent=2) + "\n"
    resolved.write_text(payload, encoding="utf-8")
    resolved.chmod(0o600)


def set_key(name: str, value: str, path: str | Path | None = None) -> None:
    """Add or update a single key in the store.

    :param name: The key name.
    :param value: The secret value (never logged or echoed).
    :param path: Store path override; defaults to :data:`STORE_PATH`.
    """
    store = load_store(path)
    store[name] = value
    write_store(store, path)


def unset_key(name: str, path: str | Path | None = None) -> bool:
    """Remove a key from the store.

    :param name: The key name to remove.
    :param path: Store path override; defaults to :data:`STORE_PATH`.
    :returns: ``True`` if the key was present and removed, ``False`` if absent.
    """
    store = load_store(path)
    if name not in store:
        return False
    del store[name]
    write_store(store, path)
    return True


def _environ(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    """Return the environment mapping to consult (`os.environ` by default)."""
    return os.environ if environ is None else environ


def get(
    name: str,
    *,
    path: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """Resolve a key value with ``os.environ`` > store > ``None`` precedence.

    :param name: The key name.
    :param path: Store path override; defaults to :data:`STORE_PATH`.
    :param environ: Environment mapping override (for tests); defaults to
        :data:`os.environ`.
    :returns: The resolved value, or ``None`` if unset in both sources.
    """
    env = _environ(environ)
    if name in env:
        return env[name]
    return load_store(path).get(name)


def source_of(
    name: str,
    *,
    path: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """Report *where* a key would resolve from — without exposing its value.

    :param name: The key name.
    :param path: Store path override; defaults to :data:`STORE_PATH`.
    :param environ: Environment mapping override; defaults to :data:`os.environ`.
    :returns: ``"env"`` if an environment variable would win, ``"store"`` if the
        store would supply it, or ``None`` if it is unset everywhere.
    """
    env = _environ(environ)
    if name in env:
        return "env"
    if name in load_store(path):
        return "store"
    return None


def scoped_env(
    names: Iterable[str],
    *,
    path: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build a least-privilege ``env`` dict of only the requested, present keys.

    Intended for handing to a child process: it contains *only* the named
    secrets that actually resolve (via :func:`get` precedence), and nothing else
    from the store.

    :param names: The key names the job is allowed to see.
    :param path: Store path override; defaults to :data:`STORE_PATH`.
    :param environ: Environment mapping override; defaults to :data:`os.environ`.
    :returns: A ``{name: value}`` dict of the present requested secrets.
    """
    result: dict[str, str] = {}
    for name in names:
        value = get(name, path=path, environ=environ)
        if value is not None:
            result[name] = value
    return result


def rclone_config_env(remote: str, params: Mapping[str, str]) -> dict[str, str]:
    """Translate rclone remote parameters to ``RCLONE_CONFIG_<REMOTE>_<KEY>`` vars.

    rclone reads a remote's configuration from environment variables of this
    shape, so a mirror can run with no config file on disk.

    :param remote: The rclone remote name (upper-cased in the variable names).
    :param params: The remote's config parameters (e.g. ``type``, ``token``).
    :returns: The corresponding ``RCLONE_CONFIG_*`` environment mapping.
    """
    prefix = f"{RCLONE_ENV_PREFIX}{remote.upper()}_"
    return {f"{prefix}{key.upper()}": value for key, value in params.items()}


def rclone_scoped_env(
    remote: str,
    *,
    path: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Collect the stored/env ``RCLONE_CONFIG_<REMOTE>_*`` credentials for `remote`.

    Only the variables scoped to this one remote are returned (least privilege),
    each resolved with :func:`get` precedence. An empty result means no
    credentials are stored for the remote (a ``rclone.conf`` may still cover it).

    :param remote: The rclone remote name.
    :param path: Store path override; defaults to :data:`STORE_PATH`.
    :param environ: Environment mapping override; defaults to :data:`os.environ`.
    :returns: A ``{RCLONE_CONFIG_<REMOTE>_<PARAM>: value}`` dict.
    """
    prefix = f"{RCLONE_ENV_PREFIX}{remote.upper()}_"
    candidates = {
        name
        for name in (*load_store(path), *_environ(environ))
        if name.startswith(prefix)
    }
    return scoped_env(sorted(candidates), path=path, environ=environ)
