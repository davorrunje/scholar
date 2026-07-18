# Proposal: `datasets.yml` manifest tooling — loader/validator + Croissant interop

`Status: draft (for discussion) · Date: 2026-07-18 · Skill: dataset`

## Context

The `dataset` skill keeps a single, git-tracked, public registry (`datasets.yml`)
as the source of truth for every dataset a project depends on. The schema is
defined in the skill (`../../../skills/dataset/SKILL.md`, "Manifest") and grounded
in `../../../resources/references/dataset-management-standards.md` (§2 schema, §3
tiers) and the shared base-asset record in
`../../../resources/substrate/asset-registry.md`.

Today the manifest has **no tooling**. **Interim (until the module is
implemented):** the skill orchestrates the step manually — loading with
`yaml.safe_load`, eyeballing the required fields against the table, and hand-mapping
Croissant on register/export. That is error-prone and does not scale to `audit`
across a whole manifest, nor does it give the venue-mandated Croissant round-trip
(NeurIPS D&B now requires a Croissant file) any machine backing. Once `scholar-tools`
is installed (via [`ensure-tooling`](../../../resources/ensure-tooling.md)) the skill
calls `scholar dataset …` instead.

This proposal covers **only the manifest tooling**: parsing, schema validation, and
Croissant/DataCite interop. Retrieval, the rclone mirror, fixity re-hashing, and the
resolution chain are a **separate proposal** — this tooling reads and writes
metadata and never touches bytes or the network.

## Goal

A light-dependency Python module the `dataset` skill's `register` and `audit` verbs
call, that:

1. **Loads** `datasets.yml` into typed records and reports precise, located errors.
2. **Validates** the base asset record plus tier-conditional required fields, with
   clear messages (which entry, which field, why).
3. **Ingests** a published Croissant JSON-LD to bootstrap a draft entry.
4. **Emits** a Croissant JSON-LD file per entry (or for the whole registry).
5. Round-trips **DataCite** citation fields for citability / DOI minting.

Non-goals: fetching bytes, computing SHA-256 (retrieval tooling owns hashing;
this layer validates the *shape* `sha256:<64-hex>`), rclone, tier *decisions*
(human-confirmed), or choosing a dataset for a claim (agency principle).

## Design sketch

Single module, stdlib + `pyyaml` only. No new heavy deps (no `jsonschema`,
no `pydantic`, no `datasets`); validation is hand-rolled against the documented
field table, Croissant I/O uses stdlib `json`.

```
scholar_tools/dataset/manifest.py        # module in the scholar-tools package
```

### Data model

`@dataclass` records mirroring the schema — `Manifest(mirror, datasets[])`,
`DatasetEntry(id, version, tier, license, redistributable, access, files[], …)`,
`FileRef(path, sha256, size)`, `Retrieval(kind, url)`, `Citation(...)`. Dataclasses
keep the surface stdlib-only and JSON/YAML round-trippable.

### Validation rules

- **Core (all tiers):** `id` (unique slug), `version`, `tier ∈ {A,B,C}`, `license`
  (SPDX id *or* explicit terms + URL), `redistributable: bool`,
  `access ∈ {open,gated}`, `files[]` each with `path` + `sha256` matching
  `^sha256:?[0-9a-f]{64}$`, `datasheet` (path/URL or `"N/A + <reason>"`).
- **Tier-conditional:** `source`/`retrieval` required for **Tier B** (and
  `retrieval.kind ∈ {http,doi,openml,git-lfs,manual}`); acquisition `instructions`
  required for **Tier C**; `sensitivity` required if PII/confidential.
- **Cross-entry:** duplicate `id` detection; `redistributable=false` with `tier: A`
  is a hard error (tier follows license, not convenience).
- Errors accumulate (report all, not first-fail) and are formatted as
  `entry '<id>': <field>: <reason>`; validation returns a structured result the
  `audit` verb renders as a gap report.

### Croissant mapping (registry ⇄ JSON-LD, schema.org/Dataset)

| Registry | Croissant |
|---|---|
| `id`, `title`/`description` | `name`, `description` |
| `version` | `version` |
| `license` (SPDX) | `license` |
| `citation` (DataCite 6-tuple) | `citeAs` |
| `pid` | `sameAs` / `identifier` (DOI) |
| `files[].path` / `.sha256` / `.size` | `distribution[].contentUrl` / `.sha256` / `.contentSize` |

Registry is the **superset source of truth**; Croissant is an export/interop
format. **Ingest** fills what it can and leaves tier / retrieval / datasheet /
sensitivity as `TODO` for the human on register. **Emit** produces a valid
`@context`/`@type: Dataset` document; fields with no registry value are omitted
rather than emitted empty.

### DataCite

`citation` is the DataCite 6-mandatory tuple (Identifier/DOI, Creator, Title,
Publisher, PublicationYear, ResourceType=Dataset). Validation warns (not errors)
when incomplete, since a citable record may not yet exist; `emit` maps it to
`citeAs`; the tuple is the minimum to mint a DOI at a public archive.

### API / CLI the skill verbs call

Importable from `scholar_tools.dataset.manifest`:

```python
load(path) -> Manifest                       # parse + structural decode; raises with line context
validate(manifest) -> ValidationReport       # all rule violations, per entry
entry_from_croissant(json_ld) -> DatasetEntry # ingest → draft (partial, flags TODOs)
croissant_for(entry) -> dict                  # emit one entry's JSON-LD
```

Exposed under the `scholar dataset` command group:

```
scholar dataset validate [datasets.yml]              # register/audit gate; exit!=0 on error
scholar dataset ingest <croissant.json> [--into datasets.yml]
scholar dataset emit <id> [-o <id>.croissant.json]   # or --all
```

- `register` calls `ingest` (if a Croissant is supplied) then `validate` on the new
  entry before writing; the human still confirms tier + license.
- `audit` calls `validate` across every entry and folds the report into its
  fixity/presence/completeness output.

## Dependencies & posture

- **Deps:** `pyyaml` + stdlib `json` only. No `jsonschema`, no `pydantic`, no
  network, no crypto. Fits the plugin's light posture (asset-registry.md,
  "Plugin vs. consumer": the plugin owns the schema + loader/validator).
- **Read/write scope:** metadata only. Never opens data files, never hashes,
  never reaches the network — that boundary is what keeps this proposal separable
  from retrieval/mirror tooling.
- **Placement:** ships in the plugin (generic engine); consumer projects own the
  `datasets.yml` entries and blobs.

## Open questions

- Package vs. single file: start as one `manifest.py`, or split
  `croissant.py` / `schema.py` now?
- Should base-record validation be shared with `literature` (common substrate
  spine) or kept dataset-local until a second consumer exists?
- Croissant `recordSet` / RAI metadata: emit a minimal stub, or leave to the human?
- SPDX id validation — ship a small allowlist, or accept any non-empty string plus
  the explicit-terms+URL alternative?
- DataCite: v4.6 (anchored in the standards digest) vs. v4.7 — does emit need to
  declare a schema version?

## Acceptance criteria

- `load` parses a valid `datasets.yml` into typed records and raises with the
  offending line/entry on malformed YAML.
- `validate` flags every missing/invalid core field and every tier-conditional
  omission (B: source/retrieval; C: instructions; PII: sensitivity), accumulating
  all violations with `entry '<id>': <field>: <reason>` messages; exits non-zero
  from the CLI on any error.
- Duplicate `id` and `tier: A` + `redistributable: false` are hard errors.
- `emit` produces schema.org/Dataset Croissant JSON-LD whose `distribution[]`
  carries `contentUrl` + `sha256`, validated by a round-trip
  `entry → croissant → entry` that preserves core + citation fields.
- `ingest` bootstraps a draft entry from a published Croissant and marks
  tier/retrieval/datasheet/sensitivity as human-TODO.
- No dependency beyond `pyyaml` + stdlib; no network or filesystem access to data
  files during validate/emit/ingest.
- `register` and `audit` invoke `scholar dataset …`; the SKILL TODO block (~line 105)
  is updated to point at the CLI instead of the interim manual workaround.

## Links

- Skill: `../../../skills/dataset/SKILL.md` (Manifest, Tiers; TODO ~line 105)
- Standards digest: `../../../resources/references/dataset-management-standards.md` (§2, §3)
- Substrate base record: `../../../resources/substrate/asset-registry.md`
- Design: `../03-dataset.md`, `../04-substrate-and-contract.md`
- ADRs: `../../../decisions/0009-dataset-thin-manifest.md`, `0012-shared-substrate.md`
- Separate proposal (not this one): retrieval / rclone mirror / fixity tooling
