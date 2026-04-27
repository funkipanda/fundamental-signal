# Dashboard UI Kit

High-fidelity recreation of the Fundamental Signal web dashboard. Bloomberg/Koyfin-influenced, dark, data-dense.

## Files
- `index.html` — interactive prototype. Click rows in the summary table to swap the detail card. Change the filter segment, toggle compact density, open the watchlist modal.
- `components.jsx` — `TopBar`, `Rail`, `Counts`, `Toolbar`, `SummaryTable`, `DetailCard`, `WatchlistModal`, plus shared icons and signal helpers.
- `data.js` — realistic sample of 9 tickers across all 5 classifications, mirrors shape from `price-vs-fundamentals/output/report.py`.
- `styles.css` — component styles; consumes tokens from the root `colors_and_type.css`.

## Screens covered
1. **Screener** (main) — summary table with signal-tinted rows + sticky detail card on the right
2. **Detail card** — selected ticker: price, classification, valuation-vs-sector metrics, quality pass/fail, 52-wk range track, plain-English flags
3. **Watchlist modal** — textarea for tickers + drop-zone placeholder for .txt/.csv upload

## Interaction notes
- Row click → select ticker, detail card updates
- Filter segmented control (ALL / UNDERVALUED / …) filters rows
- Density segmented control swaps table row height 30→24 via `body.compact`
- "Edit watchlist" opens modal; "Run screen" in modal closes it (mock)
