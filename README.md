# Fundamental Signal

A stock screener that flags price-vs-fundamentals discrepancies and ranks stocks using a modified Greenblatt Magic Formula (FCFF-based). Built with Python, FastAPI, and free financial data.

## Live Demo

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/funkipanda/fundamental-signal)

## Features

### Screener Mode
Screens stocks against Damodaran sector benchmarks using 6 CFA-grounded metrics:
- **Cheapness:** Forward P/E, EV/EBITDA, FCF Yield
- **Quality:** ROE, Cash Flow Quality (OCF/NI)
- **Health:** Debt-to-Equity

Classifies each stock as: `UNDERVALUED`, `OVERVALUED`, `VALUE_TRAP`, `QUALITY_PREMIUM`, or `FAIR_VALUE`.

### Magic Formula Mode
Ranks stocks using two metrics inspired by Joel Greenblatt's Magic Formula, with FCFF replacing EBIT:
- **ROIC** = Free Cash Flow to Firm / Invested Capital (NWC + Net PP&E, excludes goodwill)
- **Earnings Yield** = FCFF / Enterprise Value

Stocks are ranked on each metric independently, then combined. Financials and negative-FCFF stocks are auto-excluded.

### Other
- S&P 500 ticker loader (from Wikipedia)
- Damodaran NYU Stern sector benchmarks (95 industries)
- Value trap detection (cheap + deteriorating quality)
- Sector-specific overrides (financials, energy, REITs)
- Dark terminal-aesthetic UI
- CLI mode (`screen.py`) and web UI (`app.py`)

## Quick Start

```bash
# Clone
git clone https://github.com/funkipanda/fundamental-signal.git
cd fundamental-signal

# Install
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run web UI
uvicorn app:app --port 8000
# Open http://localhost:8000

# Or run CLI
python screen.py AAPL MSFT JPM XOM INTC
```

## Data Sources

| Data | Source | Freshness |
|------|--------|-----------|
| Price + fundamentals | Yahoo Finance (yfinance) | TTM, ~15 min delayed |
| Balance sheet (for ROIC) | Yahoo Finance | Most recent quarterly filing |
| Sector benchmarks | Damodaran NYU Stern | Updated annually (Jan 2026) |
| S&P 500 list | Wikipedia | Cached 7 days |

## Tech Stack

- **Backend:** Python, FastAPI
- **Data:** yfinance, Damodaran Excel datasets, Finnhub (fallback)
- **Frontend:** Vanilla HTML/JS with design system from Claude Design
- **Valuation framework:** CFA curriculum (Level 1-2 Equity Valuation)

## Limitations

This is a prototype for practitioner conversations, not a production tool:
- yfinance is an unofficial scraper with no SLA
- FCFF is approximated as OCF - CapEx (technically FCFE, not FCFF)
- Sector benchmarks are annual snapshots, not live
- No filing-grounded explanations yet (planned for v2)

## License

MIT
