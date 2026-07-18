# honest-scholar

Supporting CLI/tooling for the [honest-scholar](https://github.com/davorrunje/honest-scholar)
research-workflow plugin. Distributed as `honest-scholar`; exposes the `honest-scholar`
CLI.

Per [ADR-0024](../decisions/0024-tooling-package-and-bootstrap.md), the plugin
stays pure-markdown and this package is installed **isolated** (never into a
consumer's ML environment) on demand via the
[`ensure-tooling`](../resources/ensure-tooling.md) procedure. The CLI is the
authoritative interface; a thin MCP wrapper over the same modules may follow.

## Install (development)

```bash
cd honest-scholar
uv sync
uv run honest-scholar --version
uv run honest-scholar doctor
```

Isolated install (as `ensure-tooling` does) — **PyPI-first**, with the
git-subdirectory install as the fallback for unreleased refs:

```bash
uv tool install honest-scholar                     # primary (PyPI)
# fallback — unreleased ref or PyPI unreachable:
uv tool install "git+https://github.com/davorrunje/honest-scholar.git#subdirectory=honest-scholar"
```

## CLI

```
honest-scholar --version
honest-scholar doctor                                       # environment report (implemented)
honest-scholar literature resolve | cites | refs | enrich | neighbors   # honest-scholar#1
honest-scholar dataset    register | fetch | verify | mirror | audit    # honest-scholar#2 / #3
honest-scholar defend     record                                        # honest-scholar#4
honest-scholar backlog    add | list | rank | promote | drop            # honest-scholar#5
```

Only `doctor` and `--version` are implemented; the domain sub-commands are
typed stubs exiting with code 2 and a pointer to their tracking issue.

## Develop

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```
