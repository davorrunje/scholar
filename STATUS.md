# honest-scholar — status

An honest ledger of what is **done**, **in progress**, and **planned**.
`honest-scholar` ships two independently-versioned artifacts:

- the **plugin** — the skill instruction files (`skills/*/SKILL.md`) plus
  templates, contracts, and the migrated design record (its primary deliverable);
- the **`honest-scholar` package** — the CLI those skills call, published to PyPI
  and installed isolated from your project's ML environment.

Commits are authored by **Davor Runje** with a `Co-Authored-By: Claude` trailer.

## Done

- **All 10 skills** authored and reviewed (`skills/*/SKILL.md`, each with valid
  `name`/`description` frontmatter): `research-init`, `hypothesis-exploration`,
  `hypothesis-testing`, `paper-exploration`, `paper-synthesis`, `thesis`,
  `literature`, `dataset`, `progress`, `defend`.
- **The `honest-scholar` CLI is implemented** and JSON-emitting across all groups:
  `literature` (citation graph over OpenAlex + Semantic Scholar), `dataset`
  (manifest / Croissant / SHA-256 retrieval / rclone mirror / audit),
  `defend record`, `backlog`, and `doctor` — with a strict-mypy, 100%-covered test
  suite. The design specs live under `docs/design/proposals/`.
- **Design record** migrated from the design session: `docs/design/` (meta-spec +
  4 sub-specs), `decisions/` (MADR ADRs + index), `resources/references/` (verified
  primary-source digests), and the v1 visual identity.
- **Shared resources**: experiment-backend + engineering contracts, the asset
  registry / substrate, the rigor kit, and the staged-doc templates (hypothesis /
  paper / thesis) with the `progress` status-frontmatter, rigor prompts, named
  human sign-off, and a Toulmin-sextet ledger.
- **Docs**: `README.md`, `docs/USER-GUIDE.md`, `DISCLOSURE.md`, `RELEASING.md`,
  `CONTRIBUTING.md`, and the commit-attribution / discovery convention.
- **Packaging & CI**: self-marketplace (`.claude-plugin/marketplace.json`,
  `claude plugin validate` ✔); CI matrix, coverage gate, and PyPI Trusted
  Publishing via GitHub Releases.

## In progress

- **First final release (`v0.1.0`)** — the release-readiness cleanup is underway
  (see the `v0.1.0` milestone and the linked issues). The package currently
  publishes as a pre-release (`0.0.0b0`) to TestPyPI/PyPI for validation.

## Planned

- A citable **arXiv report** describing the skills and their rationale — ideally
  written *using* `honest-scholar` itself (the preferred citation once it exists).
- Cross-repo thesis aggregation (design in `docs/design/proposals/`).

## How to review

1. Read this file + [`README.md`](README.md).
2. Skim [`docs/design/00-meta-spec.md`](docs/design/00-meta-spec.md) (the whole
   picture) and [`decisions/README.md`](decisions/README.md).
3. Read the `skills/*/SKILL.md` you care about most — suggest `defend`,
   `hypothesis-testing`, `literature`.
