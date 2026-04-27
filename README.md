# Price vs. Fundamentals Discrepancy Screener

A CLI tool that screens stocks for price-vs-fundamentals divergences using free data, applies CFA-grounded quality filters, and outputs a plain-English discrepancy report.

## Quick Start

```bash
cd prototypes/price-vs-fundamentals

# Install dependencies
pip install -r requirements.txt

# Screen specific tickers
python screen.py AAPL MSFT JPM XOM INTC

# Screen from a watchlist file
python screen.py --watchlist watch.txt

# Also generate a markdown report
python screen.py AAPL MSFT --output md
```

## Optional: Finnhub Fallback

If yfinance rate-limits you, add a free Finnhub API key:

```bash
cp .env.example .env
# Edit .env and add your key from https://finnhub.io/register
```

## What It Does

1. Pulls fundamental data (P/E, EV/EBITDA, FCF, ROE, etc.) from Yahoo Finance
2. Compares to sector benchmarks from Damodaran (NYU Stern)
3. Applies a 6-metric composite score: cheapness + quality + financial health
4. Classifies each stock: UNDERVALUED, OVERVALUED, VALUE_TRAP, QUALITY_PREMIUM, or FAIR_VALUE
5. Outputs a formatted terminal report with detail cards for interesting signals

## Classifications

- **UNDERVALUED** — Cheap on valuation metrics AND passes quality filters (ROE, cash flow quality)
- **VALUE_TRAP** — Cheap on metrics BUT fails quality filters — cheap for a reason
- **OVERVALUED** — Expensive on metrics with no quality justification
- **QUALITY_PREMIUM** — Expensive on metrics BUT strong quality — market pricing in growth
- **FAIR_VALUE** — No significant divergence from sector norms
