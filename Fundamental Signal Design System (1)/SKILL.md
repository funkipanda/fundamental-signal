---
name: fundamental-signal-design
description: Use this skill to generate well-branded interfaces and assets for Fundamental Signal, either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the README.md file within this skill, and explore the other available files.

If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.

If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

## Quick orientation

Fundamental Signal is a Bloomberg/Koyfin-styled terminal for buy-side equity analysts. Dark, data-dense, monospace-forward. Five-way classification with strict color mapping:

| Signal | Color | Use |
|---|---|---|
| UNDERVALUED | green `#22c55e` | cheap + quality passes |
| OVERVALUED | red `#ef4444` | expensive everywhere |
| VALUE_TRAP | amber `#f59e0b` | cheap but quality fails |
| QUALITY_PREMIUM | cyan `#22d3ee` | rich multiples, strong fundamentals |
| FAIR_VALUE | slate `#94a3b8` | near sector norms |

## Files in this skill

- `README.md` — full guidelines (content, visual foundations, iconography, index)
- `colors_and_type.css` — CSS variables for color + type; import at the top of any artifact
- `fonts/` — JetBrains Mono + Inter webfonts (Google Fonts, see caveats in README)
- `assets/` — logos, monogram, signal icons
- `preview/` — design-system cards (type, color, spacing, components, brand)
- `ui_kits/dashboard/` — interactive screener prototype + reusable React components

## Rules

- Always `<link rel="stylesheet" href="colors_and_type.css">` before component CSS
- Numbers always `font-variant-numeric: tabular-nums` and use `--fs-font-mono`
- Never use a signal color for decoration — it must encode meaning
- Prefer 1–2px borders over shadows; reserve shadows for floating surfaces
- Icons are 1.5px stroke Lucide-style SVG — never emoji
- N/A and suppressed metrics render as dim gray `N/A`, never `0` or `—`
