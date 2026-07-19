# Visual identity

Honest Scholar's identity is built to read as rigorous, not decorative: a deep
indigo grounds the system in credibility, a single coral accent carries every
call to action and moment of confirmation — the checkmark, the sign-off, the
"verified." Quietly confident and understated, it is built for researchers
evaluating a new tool, not for a landing page.

This page is the design-record narrative. The **canonical asset spec** — exact
roles, sizes, clearspace, and the source SVGs — lives alongside the assets in
[`assets/visual-identity.md`](../../assets/visual-identity.md); keep the two in
sync (palette and asset roles here must match it).

## Logo

![Wordmark lockup on a light surface](../../assets/wordmark-lockup-light.svg)

The icon mark ([`assets/icon-mark.svg`](../../assets/icon-mark.svg)) is a coral
circle with a white checkmark, used standalone as the favicon and app icon at
32/24/16px, and paired with the wordmark in the lockups:

- [`wordmark-lockup-light.svg`](../../assets/wordmark-lockup-light.svg) — indigo
  wordmark, for **light** surfaces (docs in light mode, README body).
- [`wordmark-lockup-dark.svg`](../../assets/wordmark-lockup-dark.svg) — white
  wordmark with the coral mark, for **dark** surfaces (docs in dark mode).

**Clearspace & minimum size.** Keep clearspace equal to the icon's radius on
every side. Never render the lockup narrower than 120px, or the icon alone below
16px. Don't recolor the mark, stretch or skew the lockup, add shadows or
outlines, or place it on busy imagery.

## Color

| Name | Hex | Usage |
|---|---|---|
| Indigo | `#241852` | Primary — headers, dark surfaces, wordmark text on white |
| Coral | `#ff6558` | Accent — the mark, CTAs, confirmations. Never for large fills |
| White | `#ffffff` | Base for docs, README body, light surfaces |
| Ink | `#3a3350` | Body text on white |
| Muted | `#8b7fae` | Captions, secondary labels |

Coral is deliberately reserved for **confirmation** — the checkmark, the signed
sign-off, the "verified" — reinforcing the principle that a decision is real only
once a human signs it (agency; ADR-0016). It is an accent, never a fill: one
coral moment per view.

## Typography

- **Display — Space Grotesk** (500–700): headlines, wordmark, section labels.
- **Body — Source Sans 3** (400–700): docs, README prose, UI copy.
- **Mono — JetBrains Mono**: code, CLI commands, badges, skill names, run-refs —
  the machine parts.

## Applications

- **README header** — the banner ([`assets/wordmark-banner.svg`](../../assets/wordmark-banner.svg)),
  centred at ~640px.
- **Docs site** — `docs.json` uses the indigo primary, the light-surface lockup
  in light mode and the dark-surface lockup in dark mode, and the icon mark as
  the favicon. The build tool ([`tools/build_docs_site.py`](../../tools/build_docs_site.py))
  copies these assets into the generated site.
- **Badges** — flat-square style, `labelColor=241852` (indigo). Status/metric
  badges (CI, coverage) keep their signal color; static badges use `color=ff6558`
  (coral). See the shields.io URLs in the root [`README.md`](../../README.md).
- **Social preview** — [`assets/social-preview.svg`](../../assets/social-preview.svg)
  (1280×640), the GitHub repo social image / OG card.

## Voice

Rigorous, plain, anti-hype. Say what the tool does, not how exciting it is.
Quietly confident: no exclamation points, no "revolutionize," no unearned
superlatives. Precise verbs over adjectives — "traces," "retires," "verifies,"
not "seamlessly" or "powerful." This is the mentor-and-colleague register: it
advises and examines, but *you* decide and *you* author.
