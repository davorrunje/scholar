# Visual identity

Honest Scholar's identity is built to read as rigorous, not decorative: a deep
indigo grounds the system in credibility, a single coral accent carries every
call to action and moment of confirmation — the checkmark, the sign-off, the
"verified." Quietly confident, understated: built for researchers evaluating a
new tool, not for a landing page.

## Logo

<p align="center">
  <img src="wordmark-lockup-dark.svg" alt="Lockup on dark" width="380">
  &nbsp;&nbsp;
  <img src="wordmark-lockup-light.svg" alt="Lockup on light" width="380">
</p>

The icon mark (`assets/icon-mark.svg`) is a coral circle with a white
checkmark, used standalone as the favicon and app icon at 32/24/16px, and
paired with the wordmark in the lockups above.

**Clearspace & minimum size.** Keep clearspace equal to the icon's radius on
every side. Never render the lockup narrower than 120px, or the icon alone
below 16px.

**Don't:**
- Recolor the mark
- Stretch or skew the lockup
- Add drop shadows or outlines
- Place it on busy imagery

## Color

| Swatch | Name | Hex | Usage |
|---|---|---|---|
| 🟪 | Indigo | `#241852` | Primary — headers, dark surfaces, wordmark text on white |
| 🟧 | Coral | `#ff6558` | Accent — mark, CTAs, confirmations. Never for large fills |
| ⬜ | White | `#ffffff` | Base for docs, README body, light surfaces |
| ⬛ | Ink | `#3a3350` | Body text on white |
| ◻️ | Muted | `#8b7fae` | Captions, secondary labels |

## Typography

- **Display — Space Grotesk** (weights 500–700): headlines, wordmark, section labels.
- **Body — Source Sans 3** (weights 400–700): docs, README prose, UI copy.
- **Mono — JetBrains Mono**: code, CLI commands, badges, technical labels.

## Applications

**README header:**

<p align="center"><img src="wordmark-banner.svg" alt="README header" width="640"></p>

**Badges** use `labelColor=241852` (indigo) and `color=ff6558` (coral), flat-square style — see the shields.io URLs in the root `README.md`.

**Social preview** (GitHub repo social image, 1280×640):

<p align="center"><img src="social-preview.svg" alt="Social preview" width="640"></p>

## Voice

Rigorous, plain, anti-hype. Say what the tool does, not how exciting it is.
Quietly confident: no exclamation points, no "revolutionize," no unearned
superlatives. Precise verbs over adjectives — "traces," "retires," "verifies,"
not "seamlessly" or "powerful."

## Assets

All source files live in [`assets/`](../assets):

- `icon-mark.svg` — app icon / favicon source (512×512)
- `wordmark-banner.svg` — README header (1200×300)
- `wordmark-lockup-dark.svg` — horizontal lockup, transparent, for dark surfaces
- `wordmark-lockup-light.svg` — horizontal lockup, transparent, for light surfaces
- `social-preview.svg` — GitHub social preview (1280×640)
