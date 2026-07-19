<p align="center">
  <img src="assets/wordmark-banner.svg" alt="Honest Scholar" width="640">
</p>

<p align="center"><em>Research you can defend.</em></p>

<p align="center">Keep your research honest — <strong>especially now that AI is in the loop</strong>.</p>

<p align="center">
  <a href="https://github.com/davorrunje/honest-scholar/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/davorrunje/honest-scholar/ci.yml?branch=main&style=flat-square&labelColor=241852&label=CI" alt="CI"></a>
  <a href="https://codecov.io/gh/davorrunje/honest-scholar"><img src="https://img.shields.io/codecov/c/github/davorrunje/honest-scholar?style=flat-square&labelColor=241852&label=coverage" alt="coverage"></a>
</p>

---

**`honest-scholar`** gives your whole *scientific* research workflow one uniform,
git-native home inside Claude Code — idea → literature → hypothesis → test →
publish-decision → paper → thesis — so you and your collaborators work the same way
and never re-derive the workflow, or its rigor, per project. Concretely, it:

- **scouts and positions the literature** over the citation graph (OpenAlex +
  Semantic Scholar) — forward/backward citations, co-citation and
  bibliographic-coupling neighbours, a CSL-JSON bib, and a decision triage sidecar;
- **runs the hypothesis → test → publish-decision lifecycle** with every result
  traced to a run-ref, refuted ideas retired (not deleted), and named human sign-off
  on each material decision;
- **keeps datasets reproducible** — a tiered registry with SHA-256 fixity, a private
  rclone mirror, datasheets, and Croissant import/export;
- **builds and checks your understanding** with a Socratic tutor-examiner
  (`defend`) so you can actually defend the work in review;
- **delegates the *engineering*** (design, plans, code) to a bound engineering
  backend, staying domain- and tool-neutral.

Because AI is in the loop, it is also built so the science stays honestly *yours*
and defensible (see [The mechanics of honesty](#the-mechanics-of-honesty)).

> **New here?** Start with the **[User Guide](docs/USER-GUIDE.md)**.
>
> **Status: pre-release, actively developed.** The design is complete and recorded
> (see [Design & reasoning](#design--reasoning)); the skills and their supporting
> `honest-scholar` CLI are implemented. See [`STATUS.md`](STATUS.md) for the current
> ledger.

## The mechanics of honesty

Honesty here is mechanical, not a slogan. Two principles do the load-bearing work
(both grounded in the literature — see [`resources/references/`](resources/references/)):

1. **Assistants, not researchers (agency).** The skills keep the accounts, advise
   as a mentor, and discuss as a colleague — they do **not** perform independent
   research or make material scientific decisions. Every material decision (is a
   hypothesis confirmed/refuted, is a result real, is a paper worth publishing,
   what the thesis claims, is it defensible) is *yours*, recorded with a named
   sign-off. You author; the skill drafts. You cannot "run" the workflow to
   produce a paper or thesis — you drive it. **So the science is honestly *yours*.**
2. **You must understand it (understanding).** Every material claim, decision, and
   method must be understood to the standard a good mentor or reviewer expects.
   `honest-scholar` verifies *and builds* that understanding through Socratic questioning and
   teaching (the `defend` skill), and will not let work advance past a gap silently
   — including examining the *why* behind the methodology, to prevent cargo-cult
   rigor. **So "I understand my own paper" is true, not assumed.**

Around them sits the rest of the honesty kit: the **rigor kit** guards against
cargo-cult method (anti-cargo-cult), **provenance** makes evidence honest (every
number traces to a run-ref), **anti-Goodhart** keeps metrics honest (no
productivity scores to game), and **file-drawer + disclosure** discipline retires
dropped ideas rather than deleting them and discloses AI use truthfully (see
[`DISCLOSURE.md`](DISCLOSURE.md)).

## The skills

A single object×action shape at **three nested levels**:

| Level | generate | resolve |
|---|---|---|
| **hypothesis** (within a paper) | `hypothesis-exploration` | `hypothesis-testing` |
| **paper** (portfolio) | `paper-exploration` | `paper-synthesis` |
| **thesis** (optional top) | `thesis` (framing) | `thesis` (synthesis) |

Each resolve skill drives one candidate through **science-before-engineering**
staged documents, delegating the *engineering* (design, plans, code) to the bound
engineering backend via the engineering-delegation contract.

**Shared capabilities:** `literature` (scout/position over the citation graph;
CSL-JSON bib + a decision triage sidecar), `dataset` (tiered registry + private
rclone mirror + SHA-256 fixity + datasheets), and a pluggable **experiment-backend
contract**.

**Cross-cutting:** `progress` (frontmatter status + a generated, semantic
dashboard; refuted = done) and `defend` (the Socratic tutor-examiner, with
author-selectable mentor personas — never inferred from personality).

**Onboarding:** `research-init` scaffolds a fresh repo (`init`) or backfills an
existing one (`adopt`).

## Honest AI use — disclose & cite

When a paper is done you can add a truthful **AI-use disclosure** — a short,
evidence-based statement of what you and the AI each did — plus a citation to
`honest-scholar`. See [`DISCLOSURE.md`](DISCLOSURE.md) for the template, how-to-cite,
and an optional badge. [`paper-synthesis`](skills/paper-synthesis/SKILL.md)
**proactively proposes** both at finalize (after the publish decision is signed),
drafted from your provenance record — who signed off what, which run-refs back
which results. It is opt-in and author-owned: you review, edit, adopt, or decline.

The growth angle, plainly: every published paper that carries the disclosure points
other researchers to the tool. But Honest Scholar only *supports* honest disclosure
— it does **not** certify that your research is honest, and there is no seal of
honesty. The statement says what was done and links the record; readers judge.

## Install

`honest-scholar` is a Claude Code plugin; the repo is its own marketplace.

```
/plugin marketplace add davorrunje/honest-scholar
/plugin install honest-scholar@honest-scholar
```

**Enable it for a whole project** (so collaborators get it on trust) — add to the
consuming repo's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "honest-scholar": { "source": { "source": "github", "repo": "davorrunje/honest-scholar" } }
  },
  "enabledPlugins": { "honest-scholar@honest-scholar": true }
}
```

To pin a fixed release, add `"ref": "v0.1.0"` inside the marketplace `source`;
omit it to track the plugin's `main`. See [`STATUS.md`](STATUS.md) for the current
state.

## Design & reasoning

The design is captured in three complementary layers:

- **Specs** — the *what*: [`docs/design/`](docs/design/) (meta-spec + four
  sub-specs).
- **Decision log** — the *why*: [`decisions/`](decisions/) — MADR-style ADRs, each
  with the options considered and the **rejected alternatives and why**.
- **Reference digests** — the *evidence*: [`resources/references/`](resources/references/)
  — verified primary-source digests behind each skill and principle.
- **Proposals** — [`docs/design/proposals/`](docs/design/proposals/): the design
  specs for the `honest-scholar` CLI modules (now implemented) and for cross-repo
  thesis aggregation.

Also: the [User Guide](docs/USER-GUIDE.md), the commit-attribution / discovery
convention ([`resources/commit-attribution.md`](resources/commit-attribution.md)),
and the visual identity ([`docs/design/visual-identity.md`](docs/design/visual-identity.md)).

This record is intended to seed a blog post / paper explaining the skills and
their rationale — ideally written *using* `honest-scholar` itself.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). `honest-scholar`'s own development uses
`superpowers`; **using** `honest-scholar` does not require it — engineering is delegated
via the [engineering contract](resources/contracts/engineering.md).

## License

[Apache-2.0](LICENSE).
