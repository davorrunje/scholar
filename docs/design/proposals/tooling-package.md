# Proposal: `scholar-tools` package (Typer CLI, optional MCP)

`Status: draft (for discussion) · Date: 2026-07-18 · Umbrella for the supporting-script proposals`

## Context

Per ADR-0024, the plugin's executable tooling ships as **one Python package**,
not loose `scripts/*.py`. The five supporting-script proposals become **modules**
of this package; this doc is the umbrella that organizes them and defines the
shared shape (packaging, CLI, bootstrap, optional MCP). The plugin stays
pure-markdown; skills call the CLI after the [`ensure-tooling`](../../resources/ensure-tooling.md)
procedure.

## Package

`scholar-tools` (distribution name; exposes the **`scholar`** CLI). Isolated env
(ADR-0024) — free to depend on `typer` + one HTTP client + `pyyaml` + `pooch`
without touching a consumer's ML environment.

```
scholar-tools/
├── pyproject.toml                 # deps + [project.scripts] scholar = scholar_tools.cli:app + [project.entry-points] mcp
├── scholar_tools/
│   ├── core/                      # shared: http client, on-disk cache, config read, provenance
│   ├── literature/graph.py        # ← proposal: literature-citation-graph-client
│   ├── dataset/manifest.py        # ← proposal: dataset-manifest-tooling
│   ├── dataset/retrieval.py       # ← proposal: dataset-retrieval-mirror-tooling (+ rclone/pooch)
│   ├── grill/record.py            # ← proposal: grill-record-helper
│   ├── exploration/backlog.py     # ← proposal: exploration-backlog-helper
│   ├── cli.py                     # Typer app — the authoritative interface
│   └── mcp/ (later)               # thin MCP wrapper over the same modules
└── tests/
```

## CLI (authoritative)

A Typer command tree that mirrors the skill verbs; each command emits JSON:

```
scholar lit        resolve | cites | refs | enrich | neighbors
scholar dataset    register | fetch | verify | mirror | audit
scholar grill      record
scholar backlog    add | rank | promote | drop        # shared by both exploration skills
scholar --version
```

The skills invoke these via Bash (after `ensure-tooling`). Typer is consistent
with the experiment backend's CLI choice (ADR-0013).

## MCP (later)

A thin server exposing the same `core`/module functions as typed tools, declared
in `plugin.json → mcpServers` so Claude Code can auto-launch it. Deferred (ADR-0024,
CLI-first); nothing depends on it. Adding it is a wrapper, not a rewrite.

## Bootstrap

Install/upgrade is handled entirely by [`ensure-tooling`](../../resources/ensure-tooling.md):
detect `uv`→`pipx`→`python3`, install isolated + pinned (prefer `uv tool install`,
which also provisions Python), record the CLI in `.scholar/config.yml`, stop with
instructions if the env can't self-heal.

## Open questions

- **House HTTP client** (applies to `core`, used by literature + any http fetch):
  stdlib `urllib` (zero deps) vs `requests` (pooch already pulls it) vs `httpx`.
  Lean: stdlib `urllib` unless the async surface is needed. Decide once, here.
- **Distribution:** publish `scholar-tools` to PyPI, or install from the git repo
  (`uv tool install git+…`)? PyPI is cleaner for `uv tool install`; git avoids a
  release step early.
- **Names:** distribution `scholar-tools`, CLI `scholar` — confirm no clash; is
  `scholar` on PyPI free, or namespace as `scholar-research-tools`?
- **MCP timing:** ship the wrapper in v0.1, or wait for a concrete need?
- **Version pin source:** how the plugin communicates its pinned `scholar-tools`
  version to `ensure-tooling` (a `VERSION` file in the plugin, read by the skills?).

## Acceptance criteria

- [ ] `scholar-tools` skeleton: `pyproject.toml`, `core/`, Typer `cli.py`, `tests/`.
- [ ] `scholar --version` works via an isolated `uv tool` / `pipx` / venv install.
- [ ] `ensure-tooling` provisions it on a machine with only `uv` (no prior Python).
- [ ] Each module implemented per its own proposal; CLI subcommands wired.
- [ ] Skills updated: interim `scripts/*.py` / `curl` approaches replaced with
      `ensure-tooling` + `scholar …` calls.
- [ ] (Later) MCP wrapper exposing the same functions.

## Links

- ADR-0024 (this decision); `resources/ensure-tooling.md`.
- Module proposals: `literature-citation-graph-client.md`,
  `dataset-manifest-tooling.md`, `dataset-retrieval-mirror-tooling.md`,
  `grill-record-helper.md`, `exploration-backlog-helper.md`.
