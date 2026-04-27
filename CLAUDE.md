# CLAUDE.md — prototypes/price-vs-fundamentals/

## What this prototype does

A Python CLI that takes one or more stock tickers and outputs a **discrepancy report** flagging where the current market price diverges from fundamental valuation metrics. It compares each stock's multiples to sector benchmarks (Damodaran) and its own historical range, then applies a quality + cheapness composite to distinguish genuine undervaluation from value traps.

## Who it's for

**Primary:** Buy-side junior analyst or equity research associate at a small L/S equity fund, covering 20–40 names. Needs a fast "is this cheap or expensive relative to its sector and its own history?" screen.

**Secondary:** Independent RIA or family office analyst with no Bloomberg terminal.

## Thinking doc that motivated this

`thinking/Idea_price_vs_fundamentals_screener.md`

## Current state

**Not yet built.** Spec is complete (`SPEC.md`). Ready for implementation.

## Data sources

- **yfinance** — individual stock fundamentals + price (no API key)
- **Damodaran NYU datasets** — sector average P/E, P/B, EV/EBITDA (free Excel downloads, updated annually in January)
- **Finnhub** — fallback for rate-limited tickers (free API key, 60 req/min)

## Stack

- Python 3.10+
- Dependencies: `yfinance`, `pandas`, `openpyxl`, `rich` (for terminal formatting)
- No frontend. CLI only. Output is formatted terminal text + optional markdown file.

## Key design decisions

1. **6-metric composite** (Forward P/E, EV/EBITDA, FCF Yield, ROE, D/E, CF Quality) — covers cheapness, quality, and financial health dimensions per CFA framework.
2. **Sector-aware comparisons** via Damodaran benchmarks, not absolute thresholds alone.
3. **Value trap detection** — quality filters (ROE > 10%, CF Quality > 0.8) prevent flagging cheap-but-deteriorating stocks as undervalued.
4. **Sector-specific overrides** — suppress P/B for tech, suppress EV/EBITDA for banks, flag cyclicality caveats for Energy/Materials.

## What the next practitioner conversation should test

1. Is the plain-English output more useful than Koyfin/Finviz screening?
2. Would they trust a composite score derived from free data?
3. Is the real pain in the screening step, or in the filing-reading step that comes *after* screening?
4. Would they want this as a daily email / Slack alert rather than a CLI?
5. How many names do they actually need to screen simultaneously?
