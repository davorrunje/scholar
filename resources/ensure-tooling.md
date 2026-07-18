# ensure-tooling — bootstrap the `scholar` CLI

Skills that call the `scholar` CLI **must first ensure it is installed**, by
following this procedure. It is markdown the agent executes via the shell — the
plugin ships no build step. Goal: get an isolated, pinned `scholar-tools`
install with **zero footprint on the consumer's project environment**, adapting
to whatever toolchain is present, and **stopping honestly** when it can't.

Design principles: **idempotent** (never reinstall if already present),
**isolated** (its own env, never the consumer's ML env), **consent for
environment changes** (installing `uv`/Python is the user's call), **honest stop**
(explicit instructions rather than a cryptic failure).

## Procedure

1. **Fast path.** If a recorded invocation exists (`.scholar/config.yml →
   tooling.cli`) or `scholar` is on `PATH`, run `scholar --version`. If it matches
   the pinned version → **done**.
2. **Detect a toolchain**, in priority order:
   - `uv` (preferred — a single binary that can also provision Python),
   - else `pipx`,
   - else `python3` (with `venv` + `pip`).
3. **Install, isolated** (pinned `scholar-tools==<version>`):
   - `uv tool install scholar-tools==<version>` — installs Python + deps in an
     isolated tool env; or run ad hoc with `uvx scholar …`.
   - else `pipx install scholar-tools==<version>`.
   - else `python3 -m venv "$XDG_STATE_HOME/scholar/venv-<version>"` (fallback:
     `~/.local/state/scholar/…`) then that venv's `pip install scholar-tools==<version>`.
4. **Record** the resolved invocation under `.scholar/config.yml`
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
  venv — never the consumer repo's project env. This is what lets `scholar-tools`
  depend freely on `typer` / an HTTP client / `pyyaml` / `pooch` without touching
  anyone's torch/jax install.
- **Idempotency:** step 1 must be cheap; only steps 2–3 touch the network.
- **Version pinning:** the pinned version comes from the installed plugin; upgrades
  are deliberate (bump the pin), not silent.
- **rclone** (the private-mirror engine) is a separate single binary; if a skill
  needs it, ensure it by the same detect-then-instruct pattern (it is not a Python
  dependency).
