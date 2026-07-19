# ensure-tooling — bootstrap the `honest-scholar` CLI

Skills that call the `honest-scholar` CLI **must first ensure it is installed**, by
following this procedure. It is markdown the agent executes via the shell — the
plugin ships no build step. Goal: get an isolated, pinned `honest-scholar`
install with **zero footprint on the consumer's project environment**, adapting
to whatever toolchain is present, and **stopping honestly** when it can't.

Design principles: **idempotent** (never reinstall if already present),
**isolated** (its own env, never the consumer's ML env), **consent for
environment changes** (installing `uv`/Python is the user's call), **honest stop**
(explicit instructions rather than a cryptic failure).

## Procedure

1. **Fast path.** If a recorded invocation exists (`.honest-scholar/config.yml →
   tooling.cli`) or `honest-scholar` is on `PATH`, run `honest-scholar --version`. If it matches
   the pinned version → **done**.
2. **Detect a toolchain**, in priority order:
   - `uv` (preferred — a single binary that can also provision Python),
   - else `pipx`,
   - else `python3` (with `venv` + `pip`).
3. **Install, isolated** — **PyPI-first**. The primary source is the published
   package `honest-scholar` on PyPI, pinned to a **compatible range**
   (`honest-scholar>=0.1.0,<0.2.0` — the minimum package version this plugin
   release requires, up to the next incompatible boundary; see the *Version
   pinning* note):
   - `uv tool install honest-scholar` — installs Python + deps in an isolated tool
     env; or run ad hoc with `uvx honest-scholar …` (no persistent install).
   - else `pipx install honest-scholar`.
   - else `python3 -m venv "$XDG_STATE_HOME/honest-scholar/venv-<ref>"` (fallback:
     `~/.local/state/honest-scholar/…`) then that venv's `pip install honest-scholar`.
   - **Pre-release validation:** install release candidates from **TestPyPI**
     (`uv tool install --index https://test.pypi.org/simple/ honest-scholar`, or
     `pip install --index-url https://test.pypi.org/simple/ honest-scholar`) before
     a real release.
   - **Fallback — git subdirectory** (an unreleased `<ref>`, or PyPI unreachable):
     install from the plugin repo's `honest-scholar/` subdirectory, pinned to
     `<ref>` — a git tag/commit. Let
     `SRC="git+https://github.com/davorrunje/honest-scholar.git@<ref>#subdirectory=honest-scholar"`
     and use `uv tool install "$SRC"` / `uvx --from "$SRC" honest-scholar …` /
     `pipx install "$SRC"` / venv + `pip install "$SRC"`.
4. **Record** the resolved invocation under `.honest-scholar/config.yml`
   (`tooling: { cli: "<path-or-command>", version: "<version>" }`) so later calls
   skip detection.
5. **Environment changes need consent.** If neither `uv`/`pipx` nor Python is
   present, do **not** silently `curl … | sh` or mutate the system. Show the
   official install command (e.g. the `uv` installer one-liner) and ask the user
   to run it (or confirm) — then resume.
6. **Honest stop.** If the environment can't be provisioned (offline, locked
   down, no toolchain and consent declined) → stop and print copy-pasteable
   instructions. Never fake tooling output.

## Notes

- **Isolation:** the install lives in a `uv`/`pipx` tool env or a per-user state
  venv — never the consumer repo's project env. This is what lets `honest-scholar`
  depend freely on `typer` / `requests` / `pyyaml` / `pooch` without touching
  anyone's torch/jax install.
- **Idempotency:** step 1 must be cheap; only steps 2–3 touch the network.
- **Version pinning:** the plugin and the `honest-scholar` package are versioned
  **independently** (ADR-0026). The plugin pins a *compatible range* (currently
  `>=0.1.0,<0.2.0`), not an exact string-lock — the lower bound is the minimum
  package version the plugin's skills need (bump it deliberately when a skill
  starts using a new CLI capability), the upper bound the next incompatible
  boundary. The package's own releases (PEP 440, `v*` tags → PyPI) proceed on
  their own cadence.
- **rclone** (the private-mirror engine) is a separate single static binary — **not
  a Python dependency**; `honest-scholar` shells out to it. It is **optional**: only
  private-mirror operations need it (Tier-A git/LFS and Tier-B `pooch` fetch do
  not). Ensure it by the same **detect → ensure/instruct** pattern: check `rclone`
  on `PATH`; if missing, prefer an OS package (`apt`/`brew`), else offer to fetch
  the **checksum-verified** static binary into `$XDG_STATE_HOME/honest-scholar/bin/` **with
  consent**, else **honest stop** with the official install command (never a silent
  `curl | sh`). `honest-scholar doctor` reports Python / `uv` / `rclone` presence + versions.
