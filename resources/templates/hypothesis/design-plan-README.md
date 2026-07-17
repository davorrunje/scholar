<!-- Not a template — a pointer. design.md and plan.md are DELEGATED. -->

# design.md / plan.md — delegated to `superpowers`

`scholar` ships **no template** for the design/plan stage of a hypothesis. This
stage is **engineering**, and engineering is delegated (ADR-0002): the science is
settled in `strategy.md`, then the how-to-build-it is handed to `superpowers`.

## What to do

After `strategy.md` is written **and grilled**:

1. Run `superpowers` **`brainstorming`** to explore the experiment design.
2. Run `superpowers` **`writing-plans`** to produce the stepwise plan.
3. Store the resulting `design.md` and `plan.md` **in this hypothesis folder**
   (`docs/research/<paper>/hypotheses/<YYYY-MM-DD-slug>/`), alongside the other
   staged docs.
4. Execute the plan; execution produces the backend **run-refs** that
   `findings.md` cites.

## Guardrails

- **Science before engineering.** No design/plan until `strategy.md` exists and its
  grill gaps are resolved.
- `scholar` does not design experiments, write plans, or implement — it composes
  with `superpowers` for all of that.

The paper-level analog (`outline.md` / `plan.md`) is delegated the same way from
`paper-synthesis`. See `../../../docs/design/01-lifecycle.md` §2 and the
`hypothesis-testing` skill (`../../../skills/hypothesis-testing/SKILL.md`).
