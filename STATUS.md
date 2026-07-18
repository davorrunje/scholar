# scholar — build status

Built 2026-07-17/18 (initial cut autonomously while the author was away, then
extended). Commits are authored by **Davor Runje** with `Co-Authored-By: Claude`,
unsigned. Released `v0.0.0`.

This file is the honest ledger of what is **done**, **drafted**, or **pending**.
`scholar` is a Claude Code plugin: its primary deliverable is the **skill
instruction files** (`skills/*/SKILL.md`) plus templates, contracts, and the
migrated design record. There is intentionally little heavy Python — skills
orchestrate existing tools (git, gh, rclone, curl→OpenAlex/Semantic Scholar,
pandoc) and delegate engineering to the bound engineering backend via the
engineering-delegation contract.

## Done

- Public repo created (`davorrunje/scholar`), Apache-2.0.
- Plugin manifest (`.claude-plugin/plugin.json`), README, `.gitignore`.
- Design record migrated from the design session:
  - `docs/design/` — meta-spec + 4 sub-specs.
  - `decisions/` — 22 MADR ADRs + index.
  - `resources/references/` — 8 verified-source digests.
  - `assets/` + `docs/design/visual-identity.md` — v1 visual identity.
- **All 10 `skills/*/SKILL.md`** authored from the sub-specs (each with valid
  `name`/`description` frontmatter): `research-init`, `hypothesis-exploration`,
  `hypothesis-testing`, `paper-exploration`, `paper-synthesis`, `thesis`,
  `literature`, `dataset`, `progress`, `defend`.
  *(The commit that introduced them says "7 skill files" — a cosmetic undercount;
  all 10 landed in that commit.)*
- Shared resources: `resources/contracts/experiment-backend.md`,
  `resources/substrate/asset-registry.md`, `resources/rigor/rigor-kit.md`.
- `resources/templates/` — 12 staged-doc templates (hypothesis / paper / thesis)
  with the `progress` status-frontmatter, rigor prompts in strategy/findings,
  named human sign-off on material-decision docs, and a Toulmin-sextet ledger.
- **Released `v0.0.0`** — self-marketplace (`.claude-plugin/marketplace.json`,
  `claude plugin validate` ✔); install via `/plugin marketplace add davorrunje/scholar`
  then `/plugin install scholar@scholar`. mononet enables it in `.claude/settings.json`
  (mononet PR #131).
- **`docs/USER-GUIDE.md`** — end-to-end onboarding (install → `research-init` →
  the hypothesis/paper/thesis loop → progress/defend), domain-neutral example.
- **Commit attribution / discovery** — `resources/commit-attribution.md` + a
  `## Commit attribution` footer on every skill (`Generated-with: scholar` +
  `Scholar-Skill:` trailers).
- **`docs/design/proposals/`** — 6 first-draft specs (for discussion) for the
  supporting-script TODOs + cross-repo thesis aggregation. Each is tracked by an
  issue: **scholar#1–5** (literature graph client; dataset manifest tooling;
  dataset retrieval/mirror; defend record helper; exploration backlog helper) and
  **mononet#132** (cross-repo aggregation).

## Pending (needs the author, or a follow-up)

- **Review of every SKILL.md** — first-cut drafts; adjust tone/behavior, esp. the
  `defend` guardrail and the agency/understanding wording.
- **Discuss the 6 draft proposals**, then implement the supporting scripts
  (tracked: scholar#1–5, mononet#132). Currently each skill uses an interim
  tool-orchestrated approach.
- Plan-time open items from the sub-specs (ledger schema, status-frontmatter
  fields, `.scholar/` naming, thesis-milestone schema, the engineering-backend
  delegation seam).
- Reconcile with PR #128's four earlier research-workflow reference docs in
  `mononet` (superseded by this repo — close/repoint).

## How to review in the morning

1. Read this file + `README.md`.
2. Skim `docs/design/00-meta-spec.md` (the whole picture) and `decisions/README.md`.
3. Read the `skills/*/SKILL.md` you care about most first — suggest `defend`,
   `hypothesis-testing`, `literature`.
4. Anything wrong or off-tone: it is all committed in small steps, easy to amend.
