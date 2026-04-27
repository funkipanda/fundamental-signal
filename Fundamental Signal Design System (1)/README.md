# Fundamental Signal — Design System

AI-native stock screener that flags discrepancies between market price and fundamental valuation metrics. This design system captures the visual language for converting the CLI prototype to a practitioner-facing web dashboard.

> **Audience for the product:** Buy-side junior analyst at a small long/short equity fund, covering 20–40 names. Needs a fast "is this cheap or expensive relative to its sector?" screen. Should feel like Bloomberg Terminal or Koyfin — dense, professional, monospaced numbers, dark. Not Robinhood.

---

## Index

- `README.md` — this file (product context, content rules, visual foundations, iconography)
- `colors_and_type.css` — CSS variables for colors, typography, spacing, radii, shadows, motion
- `SKILL.md` — Agent Skill entry point (cross-compatible with Claude Code)
- `preview/` — small HTML cards registered into the Design System tab (one sub-concept per card)
- `assets/` — logo, icons, brand marks
- `ui_kits/dashboard/` — high-fidelity recreation of the web dashboard (summary table, detail card, watchlist) — `index.html` is the clickable prototype
- `fonts/` — intentionally empty; fonts loaded from Google Fonts (see Caveats)

---

## Product context

**Fundamental Signal** screens stocks for price-vs-fundamentals divergences. The CLI already exists (Python, `rich` terminal output); we are building the web dashboard practitioners will see in demos.

**Five classifications** map 1:1 to five colors — these are the heart of the system:

| Classification      | Color  | Meaning                                                                |
| ------------------- | ------ | ---------------------------------------------------------------------- |
| `UNDERVALUED`       | green  | Cheap on valuation **and** passes quality filters                      |
| `OVERVALUED`        | red    | Expensive on valuation with no quality justification                   |
| `VALUE_TRAP`        | yellow | Cheap on valuation **but** fails quality filters — cheap for a reason  |
| `QUALITY_PREMIUM`   | cyan   | Expensive on valuation **but** strong quality — market pricing growth  |
| `FAIR_VALUE`        | gray   | No significant divergence from sector norms                            |

**Core views** (per spec):

1. **Summary table** — all tickers, signal, confidence, 6 key metrics vs sector
2. **Detail card** — per-ticker valuation vs sector, quality pass/fail, price context, plain-English flags
3. **Watchlist input** — text field + file upload for tickers

### Source materials

- **Codebase (read-only):** `price-vs-fundamentals/` — Python CLI. Source of truth for data structure, classifications, thresholds, and output layout intent.
  - `SPEC.md` — full technical spec including ASCII mockups of the terminal report and detail card
  - `output/report.py` — `rich` formatter with exact color assignments + icons (`▼ UNDERVALUED`, `⚠ VALUE TRAP`, `▲ OVERVALUED`, `★ QUALITY PREMIUM`, `― FAIR VALUE`)
  - `config.py` — all thresholds, sector overrides, metric definitions
  - `analysis/scorer.py` — classification logic and flag generation
  - `reports/2026-04-23_screener.md` — sample real output

---

## CONTENT FUNDAMENTALS

Voice: **practitioner-to-practitioner. CFA-grounded. Unemotional.** We are talking to a junior analyst who already knows what a P/E is. No hand-holding, no marketing flavor.

### Tone & register

- **Third-person, observational.** "Trading at a discount to sector on 2/3 valuation metrics." Not "You should consider…" and not "We think this stock is…"
- **Plain-English with financial precision.** Flags read like an analyst's margin note, not a chatbot.
- **No hedging filler.** "Cheap for a reason? Investigate before buying." — direct imperative, question as framing, not as waffle.
- **Quantified claims only.** Every qualitative statement cites a number: "ROE is 0.0% (below 10% threshold)."

### Casing conventions — this is a load-bearing rule

- **CAPS for classifications and warnings:** `UNDERVALUED`, `VALUE_TRAP`, `OVERVALUED`, `QUALITY_PREMIUM`, `FAIR_VALUE`. Also `LEVERAGE WARNING:`, `REVENUE DECLINE:`, `NEAR 52-WEEK HIGH:`, `CYCLICAL SECTOR:`. These are preserved from the CLI output and function as the tag system.
- **Sentence case for explanatory prose.** "Trading at a discount to sector on 2/3 valuation metrics."
- **Title Case for labels and column headers.** "Forward P/E", "FCF Yield", "D/E Ratio".
- **UPPERCASE mono for eyebrows and super-labels** in the UI (e.g. `VALUATION VS. SECTOR`).

### Pronouns

- Avoid "you" and "we". The dashboard reports; it does not advise. The closest it gets is an imperative: "Investigate before buying."
- Never "your portfolio" — the tool doesn't know the user's book.

### No emoji. Use unicode characters from the CLI:

- `▼` down triangle → UNDERVALUED / cheap
- `▲` up triangle → OVERVALUED / expensive
- `⚠` warning → VALUE_TRAP
- `★` star → QUALITY_PREMIUM
- `―` em-dash-ish → FAIR_VALUE
- `✓` / `✗` → quality filter pass/fail
- `·` interpunct for separators in metadata lines

### Example copy (lifted from real output)

```
INTC — Intel Corporation
OVERVALUED (medium confidence)
Sector: Technology · Industry: Semiconductors

• Expensive on 2/3 valuation metrics with deteriorating quality
•   ROE is 0.0% (below 10% threshold)
•   CF Quality is -36.3x (below 0.8x — earnings may not be backed by cash)
• NEAR 52-WEEK HIGH: trading in top 10% of range
```

Note the nested bullets with extra indent for sub-points — lifted from `rich` formatting.

### Numbers

- **Always monospace, tabular.** `font-variant-numeric: tabular-nums`.
- **Percentages one decimal**: `15.2%`.
- **Ratios one decimal with `x` suffix**: `1.1x`, `22.0x`.
- **Prices** comma thousands, 2 decimals: `$198.45`.
- **Market cap** abbreviated: `$572B`, `$1.2T`.
- **N/A** for missing data — never blank, never `—` (reserve `―` for FAIR_VALUE).
- **Sector comparison inline:** `28.5 (29)` — stock value then sector benchmark in parens. Or longform: `10.2x vs. 13.0x sector (-21.5%)`.

---

## VISUAL FOUNDATIONS

### The visual metaphor

A **terminal window on a Bloomberg-black background**. Rich's box-drawing characters (`╔╗╚╝║═╠╣`) inspired the chrome: thin single-weight borders separate regions, no drop shadows for containment. Cards feel like panels of a workstation, not iOS cards.

### Colors

- **Background is near-black** (`#07090d`), not true black. A hair of blue in the neutrals gives a terminal-CRT tint without veering to blueprint.
- **Neutral ramp is cool** — all neutrals have a slight blue cast (`#0b0e14` → `#e6eaf5`). Avoid warm grays.
- **Five signal colors are the only saturated colors.** Nothing else should compete.
  - Green `#3ddc97` — undervalued, pass, up-tick
  - Red `#ff5a6b` — overvalued, fail, down-tick
  - Yellow `#f5c84b` — value trap, caution
  - Cyan `#4ecbe3` — quality premium, info
  - Gray `#7c86a3` — fair value, neutral, dim
- **One accent color** (blue `#88a8ff`) for non-signal interaction: focus rings, selected rows, links. Kept distinct from cyan to avoid classification confusion.
- **Signal colors get three tiers each:** full saturation for the badge/icon, dim variant for borders, translucent tint (`rgba …, 0.08`) for row backgrounds. Never fill a whole card in signal color.

### Typography

- **Two families:** Inter (UI, prose, labels) and JetBrains Mono (everything numeric, tickers, tags, eyebrows).
- **Numbers are ALWAYS mono** — even inline in prose. `ROE <span class="fs-num">15.2%</span> ✓`.
- **Eyebrows are ALWAYS mono, uppercase, tracked** (`letter-spacing: 0.08em`). They look like the column titles in a terminal table.
- **Tight scale.** Body is 13px. Table cells 12px. No heading above 40px (hero numbers only). This is information density.
- **Line-height 1.45 for prose, 1.15 for headings.** Tables run at 1.0 via fixed row height (28px default, 24px compact).

### Spacing

- **4px base grid.** Most gaps are 8/12/16. Card internal padding is usually 16px (`--fs-space-4`).
- **Dense.** We're filling a dashboard, not a landing page. Prefer 12px gutters in tables, 8px between stacked metrics.
- **Row heights:** 28px default, 24px compact. These are fixed so numeric columns align perfectly.

### Borders, radii, cards

- **Borders carry the weight.** 1px hairline (`--fs-border` = `#252c40`) defines panels, tables, and cards. This is how we avoid shadow-heavy consumer UI.
- **Radii are small.** `2px` for most surfaces, `4px` for modals. Never more. Sharp corners read as "tool", rounded as "app".
- **Cards are outlined, not elevated.** `border: 1px solid var(--fs-border); background: var(--fs-bg-card);` — no shadow by default.
- **No left-border accent cards.** That trope reads consumer-blog; we tag with a classification chip instead.

### Shadows

- **Subtle and rare.** `--fs-shadow-md` exists for modals and popovers; that's it. Never on cards.
- Flat-with-borders is the look. If you find yourself adding a shadow, try a stronger border color first.

### Backgrounds

- **Solid colors only.** No gradients, no illustrations, no textures, no full-bleed imagery.
- Page bg: `--fs-black`. Panel bg: `--fs-ink-800`. Card bg: `--fs-ink-700`. Hover: `--fs-ink-600`. That's the whole system.

### Animation

- **Minimal. Functional.** 80–140ms transitions on hover/focus. Cubic `(0.2, 0.8, 0.2, 1)` easing.
- **No bounces, no slide-ins, no skeleton-shimmer theatrics.** A number updating should fade or flash briefly (140ms) in up/down color, then return to neutral.
- **Focus rings appear instantly** (no transition) — this is a keyboard-heavy app.

### Hover & press states

- **Hover:** background shifts to `--fs-bg-hover` (one step up the neutral ramp). Borders do not change. Text does not change.
- **Press:** same as hover plus 1px translate down OR slight opacity dip (0.85). Pick one per component and stick with it.
- **Row hover in tables:** background tint only. Preserve the classification row tint if present — they stack.

### Focus

- **Always visible.** 1px inner border of `--fs-accent` + 3px outer glow of `--fs-accent-bg`. See `--fs-shadow-focus`.
- Never `outline: none` without a replacement.

### Transparency & blur

- **Used for:** signal row tints (`rgba …, 0.08`), popover backdrops, modal scrims.
- **Not used for:** glassmorphic panels. This is a pro tool; clarity beats aesthetic softness.

### Layout rules

- **Left sidebar (nav) + top bar (search, density toggle, user)** is the default shell.
- **Sidebar is 48px icon-rail or 240px expanded.** Collapsible.
- **Max content width:** none. Tables expand. Embrace horizontal scroll before you shrink columns.
- **Dense toggle** should be prominent — swaps `--fs-density-row` from 28px to 24px.

---

## ICONOGRAPHY

The CLI uses **unicode characters as icons** — that's the primary iconography and we preserve it in the web UI wherever classification or status is expressed.

### Primary: unicode glyphs (keep these)

| Glyph | Meaning              | Where |
| ----- | -------------------- | ----- |
| `▼`   | undervalued / down / cheap | Signal badges, table rows, metric arrows |
| `▲`   | overvalued / up / expensive | Signal badges, table rows, metric arrows |
| `⚠`   | value trap / warning | Signal badges, CAPS warnings |
| `★`   | quality premium      | Signal badges |
| `―`   | fair value           | Signal badges |
| `✓`   | quality pass         | Detail card quality checks |
| `✗`   | quality fail         | Detail card quality checks |
| `·`   | metadata separator   | "Sector: X · Industry: Y" |

These render in monospace so they align in tables — do not swap them for icon-font icons.

### Secondary: Lucide (via CDN)

For chrome (nav, toolbars, buttons, form controls) we use **[Lucide](https://lucide.dev)** — thin 1.5px stroke, geometric, matches the terminal aesthetic. Loaded via CDN: `https://unpkg.com/lucide@latest`.

Used for: search, filter, download, settings, add, close, chevrons, upload, file, user, sidebar-toggle. **Not** for signals — those stay unicode.

**Substitution flagged:** the source codebase has no icons (CLI only). Lucide is our choice to match the thin/technical aesthetic. If the team standardizes on something else, swap here.

### No emoji. No PNG icons. No hand-drawn SVG illustrations.

---

## Caveats / substitutions

- **Fonts:** codebase does not ship any fonts. We use **JetBrains Mono** + **Inter** via Google Fonts (pinned in `colors_and_type.css`). JetBrains Mono matches the CLI's terminal-output vibe; Inter is the neutral-cool UI sans. If the team has preferred faces (e.g. IBM Plex Mono, Söhne, a Bloomberg-style proprietary face), swap the `@import` and the two `--fs-font-*` variables.
- **Icons:** no icon set exists in the source. Lucide is our pick via CDN.
- **Logo:** no logo exists in the source. We designed a simple wordmark/monogram in `assets/` — flagged as placeholder, easy to replace.
- **Product screenshots:** only ASCII mockups in `SPEC.md` and one real terminal-output markdown report. All web UI is interpretive.
