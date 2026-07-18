# Contributing to honest-scholar

## Built with `superpowers` — but honest-scholar does **not** require it

`honest-scholar`'s own development uses the [`superpowers`](https://github.com/obra/superpowers)
engineering workflow (brainstorming → writing-plans → implementation). It is
enabled for maintainers in this repo's [`.claude/settings.json`](.claude/settings.json).

**This is a maintainer choice for building *this* plugin. Using `honest-scholar` does not
require `superpowers`.** `honest-scholar` names no engineering tool: its skills delegate
engineering through the **engineering-delegation contract**
([`resources/contracts/engineering.md`](resources/contracts/engineering.md)), and
each consuming repo binds whatever engineering backend it uses (or none) via
`.honest-scholar/config.yml`. The build-vs-use line is deliberate (ADR-0023).

## Repo layout

- `skills/<name>/SKILL.md` — the plugin's skills (the primary deliverable).
- `resources/` — `contracts/` (experiment-backend, engineering), `substrate/`,
  `rigor/`, `templates/`, `references/` (verified-source digests).
- `docs/design/` — the specs (meta-spec + sub-specs) and `proposals/` (drafts).
- `decisions/` — MADR ADRs (one per decision, with rejected alternatives).
- `.claude-plugin/` — `plugin.json` + `marketplace.json`.

## Conventions

- **Record decisions as ADRs.** Any material design decision gets a MADR entry in
  `decisions/` (context · drivers · options · decision · consequences · rejected
  alternatives), linked from `decisions/README.md`.
- **Ground claims.** Methodology decisions cite `resources/references/` digests.
- **Commit attribution.** Commits of skill-produced artifacts carry the discovery
  trailers in [`resources/commit-attribution.md`](resources/commit-attribution.md).
- **Validate before publishing:** `claude plugin validate .`
- **Test-install locally:** `/plugin marketplace add ./` then
  `/plugin install honest-scholar@honest-scholar`.

## Domain-neutrality

`honest-scholar` must stay domain-neutral: no ML-, monotonic-network-, or repo-specific
assumptions in the plugin. Consumer-specific details (anchors, datasets, backends)
live in the consuming repo's config/content, never here.
