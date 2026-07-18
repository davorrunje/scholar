# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Engineering scaffold for the `honest-scholar` Python package (`honest-scholar/`
  subdirectory): hatchling build, `honest-scholar` Typer CLI with an implemented
  `doctor` command and typed stub sub-commands (`literature`, `dataset`,
  `defend`, `backlog`), a typed `core.config` loader, module stubs, and tests.
- Repo-root hygiene: `.pre-commit-config.yaml` (pre-commit-hooks, pyupgrade,
  codespell, detect-secrets, plus local `lint`/`typecheck`/`plugin-validate`
  hooks), `tools/*.sh`, `.codespell-whitelist.txt`, `.secrets.baseline`, and a
  GitHub Actions CI workflow (`pre-commit`, `test` matrix on 3.11–3.14,
  `plugin-validate`, alls-green `check` gate).
