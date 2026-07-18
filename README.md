<p align="center">
  <img src="assets/wordmark.svg" alt="scholar" width="360">
</p>

<p align="center"><em>Research you can defend.</em></p>

---

**`scholar`** is the *scientific* counterpart to
[`superpowers`](https://github.com/) (which handles *engineering*): a uniform,
git-native Claude Code plugin for the whole research lifecycle — idea → literature
→ hypothesis → test → publish-decision → paper → thesis — so a researcher and
their collaborators work the same way and re-derive neither the workflow nor its
rigor per project.

> **Status: early / work in progress.** The design is complete and recorded (see
> [Design & reasoning](#design--reasoning)); the skills are being implemented. See
> [`STATUS.md`](STATUS.md) for exactly what is done, stubbed, or pending.

## Two guiding principles

Everything in `scholar` sits under two principles (both grounded in the
literature — see [`resources/references/`](resources/references/)):

1. **Assistants, not researchers (agency).** The skills keep the accounts, advise
   as a mentor, and discuss as a colleague — they do **not** perform independent
   research or make material scientific decisions. Every material decision (is a
   hypothesis confirmed/refuted, is a result real, is a paper worth publishing,
   what the thesis claims, is it defensible) is *yours*, recorded with a named
   sign-off. You author; the skill drafts. You cannot "run" the workflow to
   produce a paper or thesis — you drive it.
2. **You must understand it (understanding).** Every material claim, decision, and
   method must be understood to the standard a good mentor or reviewer expects.
   `scholar` verifies *and builds* that understanding through Socratic grilling and
   teaching (the `grill` skill), and will not let work advance past a gap silently
   — including grilling the *why* behind the methodology, to prevent cargo-cult
   rigor.

## The skills

A single object×action shape at **three nested levels**:

| Level | generate | resolve |
|---|---|---|
| **hypothesis** (within a paper) | `hypothesis-exploration` | `hypothesis-testing` |
| **paper** (portfolio) | `paper-exploration` | `paper-synthesis` |
| **thesis** (optional top) | `thesis` (framing) | `thesis` (synthesis) |

Each resolve skill drives one candidate through **science-before-engineering**
staged documents, delegating the *engineering* (design, plans, code) to
`superpowers`.

**Shared capabilities:** `literature` (scout/position over the citation graph;
CSL-JSON bib + a decision triage sidecar), `dataset` (tiered registry + private
rclone mirror + SHA-256 fixity + datasheets), and a pluggable **experiment-backend
contract**.

**Cross-cutting:** `progress` (frontmatter status + a generated, semantic
dashboard; refuted = done) and `grill` (the Socratic tutor-examiner, with
author-selectable mentor personas — never inferred from personality).

**Onboarding:** `research-init` scaffolds a fresh repo (`init`) or backfills an
existing one (`adopt`).

## Install

`scholar` is a Claude Code plugin; the repo is its own marketplace.

```
/plugin marketplace add davorrunje/scholar
/plugin install scholar@scholar
```

**Enable it for a whole project** (so collaborators get it on trust) — add to the
consuming repo's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "scholar": { "source": { "source": "github", "repo": "davorrunje/scholar" } }
  },
  "enabledPlugins": { "scholar@scholar": true }
}
```

Pin a release with `"ref": "v0.0.0"` inside the marketplace `source` if you want a
fixed version rather than the default branch. **Status:** early — see
[`STATUS.md`](STATUS.md).

## Design & reasoning

The design is captured in three complementary layers:

- **Specs** — the *what*: [`docs/design/`](docs/design/) (meta-spec + four
  sub-specs).
- **Decision log** — the *why*: [`decisions/`](decisions/) — MADR-style ADRs, each
  with the options considered and the **rejected alternatives and why**.
- **Reference digests** — the *evidence*: [`resources/references/`](resources/references/)
  — verified primary-source digests behind each skill and principle.

Visual identity: [`docs/design/visual-identity.md`](docs/design/visual-identity.md).

This record is intended to seed a blog post / paper explaining the skills and
their rationale — ideally written *using* `scholar` itself.

## License

[Apache-2.0](LICENSE).
