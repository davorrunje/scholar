# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-07-19

First public release — a Claude Code plugin for the scientific research workflow,
plus the `honest-scholar` CLI it calls. The two artifacts are versioned
independently (ADR-0026); this is `0.1.0` for both.

### Added

- **Plugin — 10 skills** across the nested generate/resolve lifecycle:
  `hypothesis-exploration` / `hypothesis-testing`, `paper-exploration` /
  `paper-synthesis`, `thesis`, the shared `literature` and `dataset` capabilities,
  cross-cutting `progress` and `defend`, and `research-init` onboarding — behind
  the exploration→resolution firewall and the agency + understanding principles.
  Distributed via the repo's git self-marketplace.
- **`honest-scholar` package** (PyPI, installed isolated) — a Typer CLI with fully
  implemented groups: `literature` (OpenAlex + Semantic Scholar citation graph),
  `dataset` (manifest / Croissant / SHA-256 retrieval / rclone mirror / audit),
  `defend record`, `backlog`, `doctor`, `keys`, and `--version`. Strict mypy;
  **100% statement + branch test coverage** gate.
- Honest failure handling: rate-limit / transient errors are distinct from a
  genuine not-found and never surface as tracebacks; unified, gitignored API-key
  store (`keys`) with env-var precedence and least-privilege scoped env for child
  processes.
- **Rendered docs site** at [honest-scholar.science](https://honest-scholar.science)
  (Mintlify) — generated from the repo's markdown on release (user guide, skills,
  CLI reference, and the full design record), gated in CI by a real MDX compile +
  build-time and post-publish broken-link checks.
- **Design record**: the meta-spec + four sub-specs, 30 MADR ADRs, verified-source
  reference digests, and the visual identity.
- **Release & CI engineering**: independent plugin/package versioning with a
  compatibility pin (ADR-0026), GitHub-Release-driven PyPI publishing via Trusted
  Publishing / OIDC (ADR-0027), the 100% coverage gate (ADR-0028), a repo `CLAUDE.md`,
  and local `create-issue` / `create-pr` skills.
