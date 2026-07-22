# Proposal: Citation-graph client (`honest_scholar/literature/graph.py`)

`Status: implemented (designed 2026-07-18) · Skill: literature`

## Context

The `literature` skill's `scout` and `position` modes both walk one citation-graph
substrate: **OpenAlex** (keyless backbone, `mailto=` polite pool) plus **Semantic
Scholar** (S2AG — citation contexts, SciCite intents, `isInfluential`,
recommendations). Today there is no client: `../../../skills/literature/SKILL.md`
(§ *Tooling*) marks it unimplemented. **Interim (until the module is implemented):** the skill orchestrates
the graph step manually / via direct tool calls — persisting raw JSON as the
provenance root and editing `references.json` / `triage.yml` — which is
unreproducible and pushes pagination, degradation, and rate-limit handling onto the
operator. Once `honest-scholar` is installed (via
[`ensure-tooling`](../../../resources/ensure-tooling.md)) the skill calls
`honest-scholar literature …` instead.

This proposes the first cut of `honest_scholar/literature/graph.py` (exposed as
`honest-scholar literature …`): the read/enrich half of the
substrate (graph traversal + enrichment + neighbor sets). The registry
loader/appender, triage join, PRISMA-log and concept-matrix generators are noted as
out of scope here (separate proposal) so this stays focused.

## Goal

A light-dependency, JSON-emitting CLI + importable functions that give `scout`
(steps 1–5 of SKILL.md) and `position` (snowball backward+forward) everything they
need from the graph: resolve any id to a canonical work, page forward citations and
backward references, enrich with the fields ranking turns on, and compute
co-citation / bibliographic-coupling neighbor sets. Degrade to OpenAlex-only when no
S2 key is present. Reproducible: same id + filters + search date → same set.

## Design sketch

**CLI** (`honest-scholar literature <cmd> [args] --json`), each command prints one
JSON document to stdout; raw upstream responses are written to a `--provenance-dir`
as the provenance root before any enrichment. The same functions are importable
from `honest_scholar.literature.graph`.

| Command | Purpose | Key args |
|---|---|---|
| `honest-scholar literature resolve <id>` | id → canonical work | `--id` (DOI/arXiv/OpenAlex W…/S2) |
| `honest-scholar literature cites <id>` | forward citations (who cited it) | `--per-page`, `--max`, `--since` |
| `honest-scholar literature refs <id>` | backward references | `--max` |
| `honest-scholar literature enrich <id>...` | per-work metadata bundle | `--fields`, `--context` |
| `honest-scholar literature neighbors <id>` | co-citation + coupling sets | `--kind {cocite,couple,both}`, `--top` |

**Identifier resolution.** `resolve()` normalizes DOI / `arXiv:` / OpenAlex `W…` /
S2 (`CorpusId:` / SHA) to a canonical record `{openalex, doi, s2, arxiv, title,
year}`. OpenAlex is the identity anchor (its work id keys everything); S2 ids are
attached when available. Ambiguous/missing → record with `resolved: false` + reason,
never a crash.

**Forward citations** — OpenAlex `works?filter=cites:<W>&mailto=…&per-page=200`,
paginated via `cursor=*` until exhausted or `--max`. Each row carries provenance
`{source_id, via: "openalex"}`.

**Backward references** — read `referenced_works[]` off the anchor's OpenAlex record
(one call), then batch-hydrate to metadata.

**Enrich** — merge into a stable shape per work:
`{id{openalex,doi,s2,arxiv}, title, year, venue, cited_by_count, authors[],
abstract, context_snippet, intent, is_influential}`. `year/venue/counts/authors/
abstract` from OpenAlex (abstract reconstructed from its inverted index);
`context_snippet` (exact citing sentence), `intent` (SciCite:
Background/Method/Result-comparison), `is_influential` from S2
`/paper/{id}/citations?fields=contexts,intents,isInfluential,…`. Fields absent under
OpenAlex-only degrade to `null` with a top-level `degraded: ["context","intent"]`
marker — the caller records it in run provenance.

**Neighbor sets** (expose sub-fronts, SKILL.md scout step 5):
- *co-citation* — rank works co-cited with the anchor (forward sets intersected /
  counted), score = shared citing papers.
- *bibliographic coupling* — rank works sharing references with the anchor
  (`referenced_works` overlap), score = shared references (works for brand-new
  papers). Output: `[{id, score, title, year}]`, truncated to `--top`. Pure
  set arithmetic over already-fetched OpenAlex data — no extra API surface.

**Recommendations** (optional, idea expansion for scout) —
`recommendations/v1/papers/forpaper/<id>` when an S2 key is present; behind a
`recommend` subcommand, omitted here if it complicates v1.

## Dependencies & posture

Light-dep, per SKILL.md and `../../../resources/substrate/asset-registry.md`:
- **HTTP:** `requests` — the house HTTP client for `honest-scholar` (decided in
  `tooling-package.md`; already pulled by `pooch`, so zero net dep). No OpenAlex/S2
  SDKs, no graph libraries (`networkx` etc.); neighbor math is stdlib
  `set`/`collections.Counter`.
- **stdlib** for JSON and the on-disk cache; the CLI layer is **Typer** (the
  package's house CLI framework, per `tooling-package.md`), not argparse.
- `mailto=` on every OpenAlex call (polite pool); `x-api-key` header on S2 iff a key
  is configured (env / `.honest-scholar/config.yml`), else omit and degrade.
- **Rate-limits / caching:** respect OpenAlex 10 req/s + 100k/day and S2's lower
  keyless ceiling; exponential backoff on 429; a content-addressed on-disk response
  cache (keyed by URL) so re-runs are cheap and reproducible. Cache is the
  provenance root — never silently refreshed within a run.
- No PDF handling: bytes stay under the substrate's resolution chain + license gate.

## Open questions

- Abstract reconstruction from OpenAlex inverted index — always, or opt-in (size)?
- Neighbor scoring for large anchors (10k+ citers): cap the frontier, or stream +
  approximate? What `--top` default?
- S2 batch endpoint (`/paper/batch`) vs. per-id calls for hydration — batch cuts
  request count but couples to a second response shape.
- ~~Where does the cache live~~ — **settled** (ADR-0031): gitignored under
  `.honest-scholar/cache/http`, sharing the `cache_dir:`-configured root with
  the dataset substrate cache (`<cache_dir>/datasets`). TTL / invalidation
  policy is still open.
- Does `resolve` need Crossref as a DOI fallback when OpenAlex misses, or is
  OpenAlex-only acceptable for v1?

## Acceptance criteria

- [ ] `resolve` maps DOI / arXiv / OpenAlex / S2 ids to one canonical record; misses
      return `resolved: false` + reason, no crash.
- [ ] `cites` paginates OpenAlex via cursor to completion (or `--max`); `refs`
      returns hydrated `referenced_works`.
- [ ] `enrich` emits the full field bundle; `context_snippet` + `intent` +
      `is_influential` populate when an S2 key is present.
- [ ] With no S2 key, all commands succeed OpenAlex-only and set `degraded: […]`;
      no command hard-requires S2.
- [ ] `neighbors` returns co-citation and bibliographic-coupling sets with scores.
- [ ] Every command writes raw upstream JSON to `--provenance-dir` before enriching;
      `mailto=` always sent; runs are cache-backed and reproducible.
- [ ] 429/backoff handled; rate ceilings respected.
- [ ] Deps limited to `requests` + stdlib (+ `pyyaml` for config read); no
      graph/SDK libraries.

## Links

- Skill: `../../../skills/literature/SKILL.md` (§ *Tooling*)
- Scout methodology: `../../../resources/references/citation-scouting.md`
- Position methodology: `../../../resources/references/related-works-synthesis.md`
- Substrate + light-dep posture: `../../../resources/substrate/asset-registry.md`
- Skill design: `../02-literature.md` · Substrate contract: `../04-substrate-and-contract.md`
- Registry format: ADR-0008 (CSL-JSON), ADR-0020 (triage sidecar)
