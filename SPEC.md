# Technical Spec: Price vs. Fundamentals Discrepancy Flagger

> **Prototype goal:** A Python CLI that screens stocks for price-vs-fundamentals divergences using free data, applies CFA-grounded quality filters, and outputs a plain-English discrepancy report.
>
> **Time budget:** One evening (~3–4 hours).
>
> **Success criteria:** Running `python screen.py AAPL MSFT GOOGL JPM XOM` produces a readable terminal report that a buy-side junior analyst would find worth 2 minutes of their time.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                        CLI Entry                         │
│              screen.py  <TICKER> [TICKER...]             │
│              Options: --output md | --watchlist file.txt  │
└──────────────┬──────────────────────────────┬────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────┐      ┌───────────────────────────┐
│   data/fetcher.py    │      │  data/sector_benchmarks.py│
│                      │      │                           │
│  yfinance per-ticker │      │  Damodaran Excel loader   │
│  fundamentals + price│      │  P/E, P/B, EV/EBITDA by   │
│                      │      │  ~150 industry sectors     │
│  Fallback: Finnhub   │      │  Cached locally as JSON   │
└──────────┬───────────┘      └────────────┬──────────────┘
           │                               │
           ▼                               ▼
┌──────────────────────────────────────────────────────────┐
│                    analysis/scorer.py                     │
│                                                          │
│  1. Compute 6 core metrics per ticker                    │
│  2. Compare to sector benchmarks (Damodaran)             │
│  3. Apply composite scoring (quality + cheapness)        │
│  4. Classify: Undervalued / Overvalued / Fair / Trap     │
│  5. Apply sector-specific overrides                      │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                   output/report.py                        │
│                                                          │
│  Rich terminal table + per-ticker detail cards            │
│  Optional: write to markdown file                        │
└──────────────────────────────────────────────────────────┘
```

---

## 2. File Structure

```
prototypes/price-vs-fundamentals/
├── CLAUDE.md              # Per-prototype context (done)
├── SPEC.md                # This file
├── README.md              # How to run it
├── WRITEUP.md             # Post-build validation write-up (after building)
├── screen.py              # CLI entry point
├── data/
│   ├── __init__.py
│   ├── fetcher.py         # yfinance wrapper + Finnhub fallback
│   ├── sector_benchmarks.py  # Damodaran Excel loader + sector mapping
│   └── cache/             # Local cache dir (gitignored)
│       └── .gitkeep
├── analysis/
│   ├── __init__.py
│   └── scorer.py          # Metric computation + composite scoring
├── output/
│   ├── __init__.py
│   └── report.py          # Terminal + markdown report formatter
├── config.py              # Constants, thresholds, sector overrides
├── requirements.txt       # pip dependencies
├── .env.example           # Template for optional API keys
└── .gitignore             # cache/, .env, __pycache__
```

---

## 3. Data Layer

### 3.1 Individual Stock Data (`data/fetcher.py`)

**Primary source: yfinance**

```python
import yfinance as yf
import time

def fetch_stock_data(ticker: str) -> dict | None:
    """
    Fetch fundamental + price data for a single ticker.
    Returns a normalized dict or None on failure.
    """
    t = yf.Ticker(ticker)
    info = t.info  # Single call, returns 50+ fields

    # Extract with safe .get() — never assume a key exists
    return {
        "ticker": ticker,
        "name": info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "market_cap": info.get("marketCap"),

        # Valuation multiples
        "forward_pe": info.get("forwardPE"),
        "trailing_pe": info.get("trailingPE"),
        "price_to_book": info.get("priceToBook"),
        "ev_to_ebitda": info.get("enterpriseToEbitda"),
        "enterprise_value": info.get("enterpriseValue"),

        # Profitability
        "roe": info.get("returnOnEquity"),  # Already a decimal (0.15 = 15%)
        "roa": info.get("returnOnAssets"),
        "operating_margin": info.get("operatingMargins"),
        "profit_margin": info.get("profitMargins"),
        "gross_margin": info.get("grossMargins"),

        # Growth
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),

        # Financial health
        "debt_to_equity": info.get("debtToEquity"),  # NOTE: yfinance returns this as a percentage (150 = 1.5x)
        "current_ratio": info.get("currentRatio"),

        # Cash flow
        "free_cashflow": info.get("freeCashflow"),
        "operating_cashflow": info.get("operatingCashflow"),
        "net_income": info.get("netIncomeToCommon"),

        # Dividend
        "dividend_yield": info.get("dividendYield"),

        # Price context
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        "fifty_day_avg": info.get("fiftyDayAverage"),
        "two_hundred_day_avg": info.get("twoHundredDayAverage"),
        "beta": info.get("beta"),
    }
```

**Rate limiting strategy:**
- `time.sleep(1.5)` between ticker fetches
- Local JSON cache in `data/cache/{TICKER}_{DATE}.json` — skip fetch if today's cache exists
- On `YFRateLimitError` or HTTP 429: wait 10 seconds, retry once, then skip with warning

**Fallback: Finnhub** (optional, requires free API key in `.env`)
- Only activated if yfinance returns None for a critical field (forward_pe, ev_to_ebitda)
- Uses `finnhub.Client(api_key=key).company_basic_financials(ticker, 'all')`
- Maps Finnhub's field names to our normalized dict

### 3.2 Sector Benchmarks (`data/sector_benchmarks.py`)

**Source: Damodaran NYU Stern datasets**

Three Excel files, loaded once at startup, cached locally:

| File | URL | Key columns |
|------|-----|-------------|
| P/E by sector | `https://www.stern.nyu.edu/~adamodar/pc/datasets/pedata.xls` | Industry Name, Current PE, Forward PE |
| P/B by sector | `https://www.stern.nyu.edu/~adamodar/pc/datasets/pbvdata.xls` | Industry Name, PBV |
| EV/EBITDA by sector | `https://www.stern.nyu.edu/~adamodar/pc/datasets/vebitda.xls` | Industry Name, EV/EBITDA |

**Loading logic:**
```python
import pandas as pd
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "cache"
DAMODARAN_URLS = {
    "pe": "https://www.stern.nyu.edu/~adamodar/pc/datasets/pedata.xls",
    "pb": "https://www.stern.nyu.edu/~adamodar/pc/datasets/pbvdata.xls",
    "ev_ebitda": "https://www.stern.nyu.edu/~adamodar/pc/datasets/vebitda.xls",
}

def load_sector_benchmarks(force_refresh: bool = False) -> dict:
    """
    Load Damodaran sector benchmarks. Cache locally as JSON.
    Returns dict keyed by industry name → {pe, pb, ev_ebitda}.
    """
    cache_file = CACHE_DIR / "damodaran_benchmarks.json"
    if cache_file.exists() and not force_refresh:
        return json.loads(cache_file.read_text())

    # Load each Excel, extract industry → metric mapping
    # NOTE: skiprows varies by file — inspect each one to find the header row
    # Damodaran files have ~8 header rows of metadata before the data table
    ...
```

**Sector mapping challenge:**

Damodaran uses ~150 granular industry names (e.g., "Software (System & Application)"). yfinance uses Yahoo's taxonomy (~11 sectors, ~150 industries with different naming, e.g., "Software—Application").

**Mapping strategy for the prototype:**
1. Build a manual mapping dict for the 20 most common industries (covers ~80% of S&P 500 tickers)
2. For unmatched industries, fall back to broad sector-level averages (aggregate Damodaran industries by GICS sector)
3. Use fuzzy string matching (`difflib.get_close_matches`) as a last resort
4. Log unmapped industries to stderr so we can expand the mapping dict over time

```python
# Manual mapping: yfinance industry → Damodaran industry
INDUSTRY_MAP = {
    "Software—Application": "Software (System & Application)",
    "Software—Infrastructure": "Software (System & Application)",
    "Semiconductors": "Semiconductor",
    "Internet Content & Information": "Software (Internet)",
    "Banks—Diversified": "Banks (Money Center)",
    "Banks—Regional": "Banks (Regional)",
    "Oil & Gas Integrated": "Oil/Gas (Integrated)",
    "Oil & Gas E&P": "Oil/Gas (Production and Exploration)",
    "Drug Manufacturers—General": "Drugs (Pharmaceutical)",
    "Biotechnology": "Drugs (Biotechnology)",
    "Insurance—Diversified": "Insurance (General)",
    "Aerospace & Defense": "Aerospace/Defense",
    "Auto Manufacturers": "Auto & Truck",
    "Retail—Apparel & Specialty": "Retail (Special Lines)",
    "Internet Retail": "Retail (Online)",
    "Telecom Services": "Telecom Services",
    "Utilities—Regulated Electric": "Utility (General)",
    "REIT—Diversified": "REIT",
    "Medical Devices": "Healthcare Products",
    "Restaurants": "Restaurant/Dining",
    # Expand as needed — log misses to stderr
}

# Fallback: broad sector → aggregate benchmark
SECTOR_FALLBACK = {
    "Technology": {"pe": 28, "pb": 7.0, "ev_ebitda": 20},
    "Healthcare": {"pe": 22, "pb": 4.0, "ev_ebitda": 15},
    "Financial Services": {"pe": 13, "pb": 1.3, "ev_ebitda": None},  # EV/EBITDA not meaningful for financials
    "Energy": {"pe": 11, "pb": 1.5, "ev_ebitda": 6},
    "Consumer Cyclical": {"pe": 18, "pb": 3.0, "ev_ebitda": 12},
    "Consumer Defensive": {"pe": 20, "pb": 4.0, "ev_ebitda": 14},
    "Industrials": {"pe": 20, "pb": 3.5, "ev_ebitda": 13},
    "Basic Materials": {"pe": 14, "pb": 2.0, "ev_ebitda": 8},
    "Communication Services": {"pe": 17, "pb": 3.0, "ev_ebitda": 11},
    "Real Estate": {"pe": 35, "pb": 2.0, "ev_ebitda": 18},
    "Utilities": {"pe": 17, "pb": 1.8, "ev_ebitda": 11},
}
```

---

## 4. Analysis Layer

### 4.1 The 6-Metric Framework (`analysis/scorer.py`)

Each metric is computed from the fetched data, then compared to its sector benchmark.

| # | Metric | Formula from fetched data | Category | Direction |
|---|--------|--------------------------|----------|-----------|
| 1 | **Forward P/E** | `forward_pe` (pre-computed by yfinance) | Cheapness | Lower = cheaper |
| 2 | **EV/EBITDA** | `ev_to_ebitda` (pre-computed by yfinance) | Cheapness | Lower = cheaper |
| 3 | **FCF Yield** | `free_cashflow / market_cap` | Cheapness + Quality | Higher = cheaper |
| 4 | **ROE** | `roe` (pre-computed, decimal) | Quality | Higher = better |
| 5 | **Debt/Equity** | `debt_to_equity / 100` (yfinance returns as %) | Financial Health | Lower = healthier |
| 6 | **CF Quality** | `operating_cashflow / net_income` | Earnings Quality | Higher = better (>0.8 ideal) |

### 4.2 Comparison Logic

For each metric, compute a **divergence score** relative to the sector benchmark:

```python
def compute_divergence(stock_value: float, sector_value: float, direction: str) -> dict:
    """
    Returns divergence info:
    - pct_diff: how far from sector benchmark (positive = favorable)
    - signal: 'undervalued' | 'overvalued' | 'neutral'
    - strength: 'strong' | 'moderate' | 'weak'
    """
    if stock_value is None or sector_value is None:
        return {"pct_diff": None, "signal": "no_data", "strength": None}

    pct_diff = (stock_value - sector_value) / abs(sector_value) * 100

    # For "lower is better" metrics (P/E, EV/EBITDA, D/E), invert the sign
    if direction == "lower":
        pct_diff = -pct_diff

    # Classify signal strength
    if pct_diff > 30:
        return {"pct_diff": pct_diff, "signal": "undervalued", "strength": "strong"}
    elif pct_diff > 15:
        return {"pct_diff": pct_diff, "signal": "undervalued", "strength": "moderate"}
    elif pct_diff < -30:
        return {"pct_diff": pct_diff, "signal": "overvalued", "strength": "strong"}
    elif pct_diff < -15:
        return {"pct_diff": pct_diff, "signal": "overvalued", "strength": "moderate"}
    else:
        return {"pct_diff": pct_diff, "signal": "neutral", "strength": "weak"}
```

### 4.3 Composite Classification

After computing divergence for all 6 metrics, classify the stock:

```python
# Classification logic (simplified — see config.py for thresholds)

def classify_stock(metrics: dict, divergences: dict) -> dict:
    """
    Returns:
    - classification: 'UNDERVALUED' | 'OVERVALUED' | 'FAIR_VALUE' | 'VALUE_TRAP' | 'QUALITY_PREMIUM'
    - confidence: 'high' | 'medium' | 'low'
    - flags: list of plain-English explanation strings
    """
    flags = []

    # --- Cheapness signals ---
    cheap_count = sum(1 for m in ['forward_pe', 'ev_ebitda', 'fcf_yield']
                      if divergences[m]['signal'] == 'undervalued')
    expensive_count = sum(1 for m in ['forward_pe', 'ev_ebitda', 'fcf_yield']
                          if divergences[m]['signal'] == 'overvalued')

    # --- Quality signals ---
    roe_value = metrics.get('roe')
    cf_quality = metrics.get('cf_quality')
    de_ratio = metrics.get('debt_to_equity')

    quality_pass = (
        (roe_value is not None and roe_value > 0.10) and
        (cf_quality is not None and cf_quality > 0.8)
    )

    health_pass = (de_ratio is not None and de_ratio < 2.0)

    # --- Classification ---
    if cheap_count >= 2 and quality_pass and health_pass:
        classification = "UNDERVALUED"
        confidence = "high" if cheap_count == 3 else "medium"
        flags.append(f"Trading at a discount to sector on {cheap_count}/3 valuation metrics")
        flags.append(f"Quality filters pass: ROE {roe_value:.1%}, CF Quality {cf_quality:.1f}x")

    elif cheap_count >= 2 and not quality_pass:
        classification = "VALUE_TRAP"
        confidence = "medium"
        flags.append(f"Looks cheap on {cheap_count}/3 valuation metrics")
        if roe_value is not None and roe_value < 0.10:
            flags.append(f"WARNING: ROE is {roe_value:.1%} — below 10% threshold")
        if cf_quality is not None and cf_quality < 0.8:
            flags.append(f"WARNING: Cash flow quality is {cf_quality:.1f}x — earnings may not be backed by cash")
        flags.append("Cheap for a reason? Investigate before buying.")

    elif expensive_count >= 2 and quality_pass:
        classification = "QUALITY_PREMIUM"
        confidence = "medium"
        flags.append(f"Trading at a premium to sector on {expensive_count}/3 valuation metrics")
        flags.append(f"Quality is strong: ROE {roe_value:.1%} — market may be pricing in growth")

    elif expensive_count >= 2 and not quality_pass:
        classification = "OVERVALUED"
        confidence = "high" if expensive_count == 3 else "medium"
        flags.append(f"Expensive on {expensive_count}/3 valuation metrics with no quality offset")

    else:
        classification = "FAIR_VALUE"
        confidence = "low"
        flags.append("No strong valuation divergence detected — trading near sector norms")

    # --- Additional contextual flags ---
    if de_ratio is not None and de_ratio > 2.0:
        flags.append(f"LEVERAGE WARNING: D/E ratio is {de_ratio:.1f}x (above 2.0x threshold)")

    if metrics.get('revenue_growth') is not None and metrics['revenue_growth'] < -0.05:
        flags.append(f"REVENUE DECLINE: {metrics['revenue_growth']:.1%} YoY — structural concern if persistent")

    price = metrics.get('current_price')
    low_52 = metrics.get('fifty_two_week_low')
    high_52 = metrics.get('fifty_two_week_high')
    if price and low_52 and high_52 and (high_52 - low_52) > 0:
        position = (price - low_52) / (high_52 - low_52)
        if position < 0.2:
            flags.append(f"NEAR 52-WEEK LOW: trading in bottom 20% of range")
        elif position > 0.9:
            flags.append(f"NEAR 52-WEEK HIGH: trading in top 10% of range")

    return {
        "classification": classification,
        "confidence": confidence,
        "flags": flags,
    }
```

### 4.4 Sector-Specific Overrides (`config.py`)

```python
SECTOR_OVERRIDES = {
    "Technology": {
        "suppress": ["price_to_book"],  # P/B meaningless for asset-light tech
        "note": "Tech companies often trade at high P/E; focus on PEG and EV/Revenue for growth names",
    },
    "Financial Services": {
        "suppress": ["ev_to_ebitda"],  # Structural leverage makes EV/EBITDA inapplicable
        "substitute": {"ev_to_ebitda": "price_to_book"},  # P/B is primary for banks
        "note": "Banks operate at 8-20x leverage by design; D/E threshold does not apply",
        "de_threshold": None,  # Disable D/E check for financials
    },
    "Energy": {
        "cyclicality_warning": True,
        "note": "Cyclical sector: P/E is unreliable at earnings peaks/troughs. Weight EV/EBITDA more heavily.",
    },
    "Basic Materials": {
        "cyclicality_warning": True,
        "note": "Cyclical sector: current multiples may reflect peak/trough earnings, not normalized value.",
    },
    "Real Estate": {
        "suppress": ["forward_pe"],  # FFO-based valuation preferred for REITs
        "note": "REITs should be valued on P/FFO, not P/E. This screen may undercount REIT value.",
    },
}
```

---

## 5. Output Layer

### 5.1 Terminal Output (`output/report.py`)

Uses the `rich` library for formatted terminal tables and panels.

**Summary table** (printed for all tickers):

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PRICE vs. FUNDAMENTALS DISCREPANCY REPORT               ║
║                              2026-04-23                                     ║
╠═══════╦═══════════════╦════════╦════════════╦═══════════╦═══════════════════╣
║ Ticker║ Classification║ Conf.  ║ Fwd P/E    ║ EV/EBITDA ║ FCF Yield        ║
║       ║               ║        ║ (vs sect.) ║ (vs sect.)║                  ║
╠═══════╬═══════════════╬════════╬════════════╬═══════════╬═══════════════════╣
║ AAPL  ║ FAIR_VALUE    ║ low    ║ 28.5 (29)  ║ 21.3 (20) ║ 3.8%            ║
║ JPM   ║ UNDERVALUED   ║ medium ║ 10.2 (13)  ║    N/A    ║ 8.1%            ║
║ XOM   ║ VALUE_TRAP    ║ medium ║  8.5 (11)  ║ 4.8 (6)   ║ 9.2%            ║
╚═══════╩═══════════════╩════════╩════════════╩═══════════╩═══════════════════╝
```

**Detail card** (printed per ticker, only for non-FAIR_VALUE classifications):

```
┌─────────────────────────────────────────────────────────────┐
│  JPM — JPMorgan Chase & Co.                                 │
│  Sector: Financial Services | Industry: Banks—Diversified   │
│  Price: $198.45 | Market Cap: $572B                         │
├─────────────────────────────────────────────────────────────┤
│  CLASSIFICATION: UNDERVALUED (medium confidence)            │
│                                                             │
│  Valuation vs. Sector (Banks—Money Center):                 │
│    Forward P/E:   10.2x  vs.  13.0x sector  (-21.5%)  ▼    │
│    EV/EBITDA:     N/A (suppressed for financials)           │
│    FCF Yield:     8.1%   vs.   5.0% threshold  ✓           │
│                                                             │
│  Quality:                                                   │
│    ROE:           15.2%  ✓  (above 10% threshold)          │
│    CF Quality:    1.1x   ✓  (above 0.8x threshold)        │
│    D/E:           N/A (not applicable for banks)            │
│                                                             │
│  Flags:                                                     │
│    • Trading at a discount to sector on 2/3 valuation       │
│      metrics                                                │
│    • Quality filters pass: ROE 15.2%, CF Quality 1.1x      │
│    • Sector note: Banks operate at 8-20x leverage by        │
│      design; D/E threshold does not apply                   │
│                                                             │
│  Price Context:                                             │
│    52-week range: $167.20 — $215.80 (currently at 65%)     │
│    50-day avg: $192.30 | 200-day avg: $188.50              │
│    Beta: 1.05                                               │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Markdown Output (optional, `--output md`)

Same content as terminal output, written to `reports/{DATE}_screener.md`. Useful for sharing with practitioners or pasting into Obsidian.

---

## 6. CLI Interface (`screen.py`)

```python
"""
Usage:
    python screen.py AAPL MSFT GOOGL          # Screen specific tickers
    python screen.py --watchlist watch.txt      # Screen tickers from file (one per line)
    python screen.py AAPL --output md           # Also write markdown report
    python screen.py AAPL --refresh-benchmarks  # Force re-download Damodaran data
    python screen.py --help                     # Show help

Environment variables (optional, in .env):
    FINNHUB_API_KEY=your_key_here              # Enables Finnhub fallback
"""

import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Screen stocks for price vs. fundamentals discrepancies"
    )
    parser.add_argument("tickers", nargs="*", help="Stock tickers to screen")
    parser.add_argument("--watchlist", type=Path, help="File with tickers, one per line")
    parser.add_argument("--output", choices=["terminal", "md"], default="terminal")
    parser.add_argument("--refresh-benchmarks", action="store_true",
                        help="Force re-download of Damodaran sector data")

    args = parser.parse_args()

    # Collect tickers
    tickers = list(args.tickers)
    if args.watchlist:
        tickers.extend(args.watchlist.read_text().strip().split("\n"))

    if not tickers:
        parser.error("Provide at least one ticker or --watchlist file")

    # 1. Load sector benchmarks (cached)
    benchmarks = load_sector_benchmarks(force_refresh=args.refresh_benchmarks)

    # 2. Fetch data for each ticker
    stock_data = []
    for ticker in tickers:
        data = fetch_stock_data(ticker.strip().upper())
        if data:
            stock_data.append(data)
        time.sleep(1.5)  # Rate limiting

    # 3. Score each stock
    results = []
    for data in stock_data:
        metrics = compute_metrics(data)
        sector_bench = get_benchmark_for_industry(data["industry"], data["sector"], benchmarks)
        divergences = compute_all_divergences(metrics, sector_bench)
        classification = classify_stock(metrics, divergences)
        results.append({
            "data": data,
            "metrics": metrics,
            "sector_bench": sector_bench,
            "divergences": divergences,
            "classification": classification,
        })

    # 4. Output
    print_summary_table(results)
    print_detail_cards(results)

    if args.output == "md":
        write_markdown_report(results)
```

---

## 7. Configuration & Thresholds (`config.py`)

```python
# === Divergence thresholds ===
# % difference from sector benchmark to trigger a signal
STRONG_DIVERGENCE_PCT = 30   # >30% = strong signal
MODERATE_DIVERGENCE_PCT = 15 # 15-30% = moderate signal

# === Quality thresholds ===
MIN_ROE = 0.10               # 10% — below this, quality filter fails
MIN_CF_QUALITY = 0.8         # OCF/NI — below this, earnings quality concern
MAX_DEBT_TO_EQUITY = 2.0     # D/E ratio — above this, leverage warning

# === Absolute thresholds (fallback when no sector benchmark) ===
ABSOLUTE_CHEAP_PE = 10.0
ABSOLUTE_EXPENSIVE_PE = 30.0
ABSOLUTE_CHEAP_EV_EBITDA = 6.0
ABSOLUTE_CHEAP_FCF_YIELD = 0.08  # 8%
ABSOLUTE_MIN_FCF_YIELD = 0.02    # 2% — below this, expensive

# === Cache settings ===
CACHE_EXPIRY_HOURS = 12      # Re-fetch stock data after 12 hours
BENCHMARK_CACHE_DAYS = 30    # Re-download Damodaran files monthly
```

---

## 8. Dependencies (`requirements.txt`)

```
yfinance>=0.2.36
pandas>=2.0
openpyxl>=3.1
rich>=13.0
python-dotenv>=1.0
```

Optional (for Finnhub fallback):
```
finnhub-python>=2.4
```

---

## 9. Known Limitations & Future Iterations

### Limitations of this prototype

| Limitation | Why it exists | What fixes it |
|-----------|---------------|---------------|
| No filing-grounded explanations | No LLM integration in v1 | v2: feed flagged tickers to Claude with most recent 10-K/10-Q summary |
| Sector benchmarks updated annually | Damodaran publishes in January | FMP or Finnhub sector PE endpoints for daily freshness |
| yfinance can break at any time | Unofficial scraper, no SLA | Migrate to Finnhub primary + FMP fallback |
| No historical comparison vs. own 5yr avg | yfinance `.info` only gives current multiples | Use `ticker.history()` + `ticker.financials` to compute trailing multiples |
| Industry mapping is manual and incomplete | Damodaran ≠ Yahoo taxonomy | Build a comprehensive mapping CSV over time as we encounter new industries |
| No proactive monitoring / alerts | CLI = pull-based, not push-based | v2: cron job + email/Slack integration |
| Single-point-in-time snapshot | No tracking of how divergences evolve | v2: store historical scores, show trends |

### Planned v2 enhancements (after practitioner validation)

1. **LLM synthesis layer** — For each UNDERVALUED or VALUE_TRAP flag, fetch the most recent 10-Q from SEC EDGAR (via `edgartools`), extract the MD&A section, and use Claude to generate a 2-sentence explanation of what might be driving the divergence, with a specific filing citation.

2. **Historical comparison** — Compare current Forward P/E to the stock's own 5-year average Forward P/E. Flag if >1 standard deviation below mean.

3. **Watchlist monitoring mode** — Run daily via cron, store results, email/Slack a diff showing "what changed since yesterday."

4. **Piotroski F-Score integration** — Compute the full 9-criteria F-Score from financial statements. Add as a quality overlay.

---

## 10. Implementation Order

Build in this exact sequence to maintain a working state at every step:

1. **`config.py`** — Constants and thresholds. Pure data, no logic.
2. **`data/fetcher.py`** — yfinance wrapper. Test with `AAPL`. Verify all fields populate.
3. **`data/sector_benchmarks.py`** — Damodaran loader. Test that P/E, P/B, EV/EBITDA load and parse correctly. Build the industry mapping dict.
4. **`analysis/scorer.py`** — Metric computation + divergence + classification. Unit-testable with hardcoded dicts.
5. **`output/report.py`** — Terminal formatting with `rich`. Start with the summary table, then add detail cards.
6. **`screen.py`** — Wire it all together. Test with `python screen.py AAPL MSFT JPM XOM`.
7. **Markdown output** — Add `--output md` support.
8. **Finnhub fallback** — Add `.env` support and Finnhub client. Only if yfinance proves flaky during testing.

---

## 11. Test Tickers

Use these for initial testing (covers multiple sectors and expected classifications):

| Ticker | Sector | Expected behavior |
|--------|--------|-------------------|
| AAPL | Technology | Likely FAIR_VALUE or QUALITY_PREMIUM — well-covered megacap |
| MSFT | Technology | Similar to AAPL — strong quality, moderate valuation |
| GOOGL | Communication Services | Test sector mapping for Alphabet |
| JPM | Financial Services | Tests financial sector overrides (suppress EV/EBITDA, D/E) |
| XOM | Energy | Tests cyclicality caveat + value screening |
| JNJ | Healthcare | Defensive name, should screen relatively normally |
| T | Communication Services | High yield, potentially UNDERVALUED or VALUE_TRAP |
| INTC | Technology | Possible VALUE_TRAP (cheap but deteriorating margins) |
| META | Technology | Tests high-growth tech at potentially high valuations |
| BRK-B | Financial Services | Tests holding company / conglomerate handling |
