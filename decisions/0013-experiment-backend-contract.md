# ADR-0013: Experiment-backend *contract* + pluggable backend

- Status: accepted · Date: 2026-07-17 · Deciders: Davor Runje

## Context

The pipeline skills need experimental evidence, but how experiments run is
project-specific (one project's GPU fan-out means nothing to another's). The
testing layer must be decoupled and hot-swappable.

## Decision drivers

- Pipeline skills must not depend on a concrete runner.
- Projects already have — or will build — their own orchestration; the skills must
  not assume any one, and the plugin must stay domain-neutral.
- Evidence must be citable and reproducible (provenance).

## Considered options

1. **A 4-capability contract (`run` / `evidence` / `tables` / `is-current`),
   bound per project; no bundled default — the plugin ships the contract only.**
2. Bake a specific orchestrator directly into the skills.
3. Depend on an external tracker (MLflow/W&B).

## Decision

Option 1. The plugin ships the contract only and bundles **no default backend**;
each repo supplies and binds its own implementation. Docs cite opaque **run-refs**;
the provenance stamp carries dataset `id+version+sha256`; the backend stamps
evidence but never adjudicates it.

## Consequences

- Any project brings its own runner; there is no bundled default to migrate onto.
- run-ref format left opaque (open item).

## Rejected alternatives

- **Bake in a specific orchestrator** — non-reusable; couples skills to one tool
  and breaks domain-neutrality.
- **External tracker** — not git-native; heavy; provenance not repo-owned.

## Links

sub-spec 4 §3 (`../docs/design/04-substrate-and-contract.md`).
