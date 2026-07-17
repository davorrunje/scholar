# scholar — build status

Autonomous overnight build (2026-07-17). Authored by Claude; the author (Davor
Runje) was away and will review. Commits are authored as `Claude` per instruction.

This file is the honest ledger of what is **done**, **drafted**, or **pending**.
`scholar` is a Claude Code plugin: its primary deliverable is the **skill
instruction files** (`skills/*/SKILL.md`) plus templates, contracts, and the
migrated design record. There is intentionally little heavy Python — skills
orchestrate existing tools (git, gh, rclone, curl→OpenAlex/Semantic Scholar,
pandoc) and delegate engineering to `superpowers`.

## Done

- Public repo created (`davorrunje/scholar`), Apache-2.0.
- Plugin manifest (`.claude-plugin/plugin.json`), README, `.gitignore`.
- Design record migrated from the design session:
  - `docs/design/` — meta-spec + 4 sub-specs.
  - `decisions/` — 22 MADR ADRs + index.
  - `resources/references/` — 8 verified-source digests.
  - `assets/` + `docs/design/visual-identity.md` — v1 visual identity.

## In progress / this build

- `skills/*/SKILL.md` — authoring the 10 skills from the sub-specs.
- `resources/contracts/`, `resources/substrate/`, `resources/templates/`,
  `resources/rigor/` — the experiment-backend contract, the asset-substrate
  spec, staged-doc templates, and rigor checklists.

## Pending (needs the author, or a follow-up)

- **Review of every SKILL.md** — these are drafted autonomously; the author
  should read and adjust tone/behavior, especially the `grill` guardrail and the
  agency/understanding wording.
- **Any supporting scripts** (OpenAlex/Semantic Scholar client, `datasets.yml`
  loader, rclone wrappers) — kept minimal; deferred where a skill can orchestrate
  a tool directly. Flagged in the relevant SKILL.md if stubbed.
- **Install/marketplace wiring** and a first tagged release.
- Plan-time open items from the sub-specs (ledger schema, status-frontmatter
  fields, `.scholar/` naming, thesis-milestone schema, the `superpowers`
  delegation seam).
- Migrating PR #128's four research-workflow reference docs from `mononet`
  (this build re-derived the digests independently; reconcile if needed).

## How to review in the morning

1. Read this file + `README.md`.
2. Skim `docs/design/00-meta-spec.md` (the whole picture) and `decisions/README.md`.
3. Read the `skills/*/SKILL.md` you care about most first — suggest `grill`,
   `hypothesis-testing`, `literature`.
4. Anything wrong or off-tone: it is all committed in small steps, easy to amend.
