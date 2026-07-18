# Rigor kit

A cross-cutting set of checks baked into the staged documents (primarily
`strategy.md`, before engineering; enforced through `findings.md` / `decision.md`).
Every element is also a **`defend` `methodology` target** — the author must be able
to explain *why* each works, not just perform it (Understanding principle;
`docs/design/01-lifecycle.md` §3; `resources/references/understanding-and-defense.md`).

For each element: what it is, and the **understanding check** (what the author
should be able to explain — the examination seed).

## Confirmatory vs. exploratory / preregistration
Fix the analysis before seeing outcomes, and label confirmatory vs. exploratory.
**Understand:** it curbs HARKing and shrinks the "garden of forking paths"; it does
**not** forbid exploration — only mislabeling exploration as confirmation.

## Rival hypotheses + discriminating tests
State a competing explanation and a test whose outcome differs under the rival vs.
the focal hypothesis. **Understand:** a "limitation" no analysis could ever change
is not a discriminating test.

## Severity
A passed test is evidence **only if** it would very probably have failed were the
claim false. **Understand:** a test the claim passes regardless carries no weight.
(Mayo — cite explicitly if invoked.)

## Power / MDE
Set the minimum detectable effect / power **before** data. **Understand:** a null
from an underpowered design is uninformative, not evidence of no effect; "observed
power" after the fact is not meaningful.

## TOST / equivalence (for null claims)
To argue "no effect / equivalence," use two one-sided tests against a **pre-set
equivalence bound** — not a non-significant p. **Understand:** absence of evidence
≠ evidence of absence; a p-value is not an effect size. (The most cargo-culted null
claim.)

## Disclosure checklist + file-drawer
Report all conditions, exclusions, measures, and unpublished nulls. **Understand:**
selective reporting is what makes p-values and the literature unreliable.

## Per-dataset datasheets
Each dataset carries a Gebru-style datasheet (via the `dataset` skill).
**Understand:** know the dataset's collection process, biases, and limits — a
`defend` methodology target.

## Red-team pass
Adversarially review your own work before a verdict/decision (the `defend` skill
formalizes this). **Understand:** "you must not fool yourself — and you are the
easiest person to fool" (Feynman).

---

**Anti-cargo-cult stance.** Following these as rituals without understanding them
defeats their purpose. `defend --target methodology` checks the *why*; it probes
**hard** on settled errors (e.g. "a non-significant p proves no effect") and, on
genuinely **contested** choices (frequentist vs. Bayesian), only asks for a
*defensible* justification and surfaces the standard critique — it does not impose
a school. Calibrate depth to stakes: hardest on the method carrying the central
claim. "Enough" = the author can state what the method buys, name its key
assumption/limit, and answer the one canonical critique.
