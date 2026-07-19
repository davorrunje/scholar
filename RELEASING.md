# Releasing the `honest-scholar` package

How to cut a release of the **PyPI package** (the `honest-scholar/` subdirectory —
the CLI tooling). It is versioned **independently** of the Claude Code plugin
(`.claude-plugin/plugin.json`); see [Versioning](#versioning).

Everything is driven by three GitHub Actions workflows — no local build or
`twine` needed:

| Workflow | What it does |
|---|---|
| **Bump version** (`bump-version.yml`) | Compute the next PEP 440 version, open a release PR. |
| **CI** (`ci.yml`) | Lint + type-check + tests (100% coverage gate) on every PR. |
| **Publish** (`publish.yml`) | Build + upload to TestPyPI / PyPI via Trusted Publishing (OIDC). |

## Versioning

- **PEP 440.** Source of truth is `[project].version` in
  `honest-scholar/pyproject.toml`; the runtime `honest_scholar.__version__`
  derives from the installed package metadata.
- **Independent from the plugin.** The plugin (`plugin.json`) has its own version
  and pins a *compatible range* of the package via `ensure-tooling`
  (`honest-scholar>=<min>,<<next>`). Bumping the package does not bump the plugin
  and vice-versa.
- **Tag format:** `v<version>` in PEP 440 spelling, e.g. `v0.1.0`, `v0.1.0rc1`,
  `v0.0.0a2`.

## Release steps

1. **Bump the version.** Actions → **Bump version** → *Run workflow* on `main`.
   Pick:
   - `release`: `none` / `patch` / `minor` / `major` (a release bump clears any
     prerelease),
   - `pre`: `keep` / `alpha` / `beta` / `rc` / `final`.

   | want | release | pre | result (from `0.0.0a1`) |
   |---|---|---|---|
   | next alpha | none | alpha | `0.0.0a2` |
   | promote to rc | none | rc | `0.0.0rc0` |
   | cut the final | none | final | `0.0.0` |
   | start 0.1.0's alpha | minor | alpha | `0.1.0a0` |
   | patch release | patch | keep | `0.0.1` |

   It edits `pyproject.toml` and opens a **`release: honest-scholar v<version>`**
   PR (branch `release/v<version>`). The run summary shows `old → new` + the PR
   link.

2. **Review & merge the release PR** into `main` (wait for CI to pass).

3. **Validate on TestPyPI.** Actions → **Publish** → *Run workflow* with
   `target: testpypi` (the default). Check the run's **summary** for the project
   link, and optionally smoke-test the install:
   ```bash
   uv tool install --index https://test.pypi.org/simple/ honest-scholar==<version>
   honest-scholar --version
   ```

4. **Publish to PyPI.** Either:
   ```bash
   git switch main && git pull
   git tag v<version>
   git push origin v<version>        # the tag triggers Publish → PyPI
   ```
   …or Actions → **Publish** → *Run workflow* with `target: pypi`. The run
   summary/annotation shows the published `https://pypi.org/project/honest-scholar/<version>/`.

## One-time setup (already done; here for reference)

- **Trusted Publishing (OIDC, no tokens).** Registered publishers on both PyPI
  and TestPyPI for repo `davorrunje/honest-scholar`, workflow `publish.yml`,
  environments `testpypi` / `pypi`.
- **`RELEASE_PAT` secret** — a fine-grained PAT (Contents: read/write, Pull
  requests: read/write) so **Bump version** can open the release PR *and* have CI
  run on it. Without it the bump still runs but the PR won't get CI checks.

## Notes / gotchas

- **Immutable versions.** PyPI (and TestPyPI) reject re-uploading a version that
  already exists — bump to a new one rather than re-publishing.
- **Prereleases** (`aN`/`bN`/`rcN`) publish like any version; `pip`/`uv` won't
  install them by default unless asked (`--prerelease=allow` / an explicit
  `==<prerelease>`).
- **Plugin release** is separate: bump `.claude-plugin/plugin.json` when the
  plugin/skills change, and bump the package's compatibility pin in
  `ensure-tooling` when a skill starts using a new CLI capability.
