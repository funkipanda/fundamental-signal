"""
Stock data fetcher: yfinance primary, Finnhub fallback.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

import yfinance as yf

from config import CACHE_EXPIRY_HOURS

CACHE_DIR = Path(__file__).parent / "cache"


def _cache_path(ticker: str) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return CACHE_DIR / f"{ticker}_{today}.json"


def _read_cache(ticker: str) -> dict | None:
    path = _cache_path(ticker)
    if not path.exists():
        return None
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    if age_hours > CACHE_EXPIRY_HOURS:
        return None
    return json.loads(path.read_text())


def _write_cache(ticker: str, data: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(ticker).write_text(json.dumps(data, default=str))


def fetch_stock_data(ticker: str) -> dict | None:
    """
    Fetch fundamental + price data for a single ticker.
    Returns a normalized dict or None on failure.
    Uses local cache to avoid redundant API calls.
    """
    cached = _read_cache(ticker)
    if cached:
        return cached

    try:
        t = yf.Ticker(ticker)
        info = t.info
    except Exception as e:
        print(f"  [!] Failed to fetch {ticker}: {e}")
        return None

    if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
        print(f"  [!] No data returned for {ticker}")
        return None

    data = {
        "ticker": ticker,
        "name": info.get("shortName") or info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "market_cap": info.get("marketCap"),

        # Valuation
        "forward_pe": _safe_float(info.get("forwardPE")),
        "trailing_pe": _safe_float(info.get("trailingPE")),
        "price_to_book": _safe_float(info.get("priceToBook")),
        "ev_to_ebitda": _safe_float(info.get("enterpriseToEbitda")),
        "enterprise_value": info.get("enterpriseValue"),

        # Profitability
        "roe": _safe_float(info.get("returnOnEquity")),
        "roa": _safe_float(info.get("returnOnAssets")),
        "operating_margin": _safe_float(info.get("operatingMargins")),
        "profit_margin": _safe_float(info.get("profitMargins")),

        # Growth
        "revenue_growth": _safe_float(info.get("revenueGrowth")),
        "earnings_growth": _safe_float(info.get("earningsGrowth")),

        # Financial health
        "debt_to_equity": _safe_float(info.get("debtToEquity")),
        "current_ratio": _safe_float(info.get("currentRatio")),

        # Cash flow
        "free_cashflow": info.get("freeCashflow"),
        "operating_cashflow": info.get("operatingCashflow"),
        "net_income": info.get("netIncomeToCommon"),

        # Dividend
        "dividend_yield": _safe_float(info.get("dividendYield")),

        # Price context
        "fifty_two_week_high": _safe_float(info.get("fiftyTwoWeekHigh")),
        "fifty_two_week_low": _safe_float(info.get("fiftyTwoWeekLow")),
        "fifty_day_avg": _safe_float(info.get("fiftyDayAverage")),
        "two_hundred_day_avg": _safe_float(info.get("twoHundredDayAverage")),
        "beta": _safe_float(info.get("beta")),
    }

    _write_cache(ticker, data)
    return data


def fetch_stock_data_finnhub(ticker: str) -> dict | None:
    """
    Fallback fetcher using Finnhub. Requires FINNHUB_API_KEY in env.
    Only called when yfinance fails or returns None for critical fields.
    """
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key or api_key == "your_key_here":
        return None

    try:
        import finnhub
        client = finnhub.Client(api_key=api_key)
        basics = client.company_basic_financials(ticker, "all")
        quote = client.quote(ticker)
        profile = client.company_profile2(symbol=ticker)
    except Exception as e:
        print(f"  [!] Finnhub fallback failed for {ticker}: {e}")
        return None

    metric = basics.get("metric", {})
    return {
        "ticker": ticker,
        "name": profile.get("name"),
        "sector": profile.get("finnhubIndustry"),
        "industry": profile.get("finnhubIndustry"),
        "current_price": quote.get("c"),
        "market_cap": profile.get("marketCapitalization"),
        "forward_pe": _safe_float(metric.get("peTTM")),
        "trailing_pe": _safe_float(metric.get("peTTM")),
        "price_to_book": _safe_float(metric.get("pbAnnual")),
        "ev_to_ebitda": None,  # Not directly available; would need computation
        "enterprise_value": None,
        "roe": _safe_float(metric.get("roeTTM")),
        "roa": _safe_float(metric.get("roaTTM")),
        "operating_margin": _safe_float(metric.get("operatingMarginTTM")),
        "profit_margin": _safe_float(metric.get("netProfitMarginTTM")),
        "revenue_growth": _safe_float(metric.get("revenueGrowthTTMYoy")),
        "earnings_growth": _safe_float(metric.get("epsGrowthTTMYoy")),
        "debt_to_equity": _safe_float(metric.get("totalDebtToEquityQuarterly")),
        "current_ratio": _safe_float(metric.get("currentRatioQuarterly")),
        "free_cashflow": None,
        "operating_cashflow": None,
        "net_income": None,
        "dividend_yield": _safe_float(metric.get("dividendYieldIndicatedAnnual")),
        "fifty_two_week_high": _safe_float(metric.get("52WeekHigh")),
        "fifty_two_week_low": _safe_float(metric.get("52WeekLow")),
        "fifty_day_avg": None,
        "two_hundred_day_avg": None,
        "beta": _safe_float(metric.get("beta")),
    }


def fetch_with_fallback(ticker: str) -> dict | None:
    """Fetch from yfinance, fall back to Finnhub if critical fields are missing."""
    data = fetch_stock_data(ticker)
    if data is None:
        print(f"  [~] Trying Finnhub fallback for {ticker}...")
        data = fetch_stock_data_finnhub(ticker)
    elif data.get("forward_pe") is None and data.get("ev_to_ebitda") is None:
        print(f"  [~] yfinance returned sparse data for {ticker}, trying Finnhub...")
        fb = fetch_stock_data_finnhub(ticker)
        if fb:
            for key, val in fb.items():
                if data.get(key) is None and val is not None:
                    data[key] = val
            _write_cache(ticker, data)
    return data


def fetch_magic_formula_data(ticker: str) -> dict | None:
    """
    Fetch balance sheet data needed for the FCFF-based Magic Formula.
    Returns FCFF, Enterprise Value, Invested Capital (Greenblatt), Total Assets.
    """
    cache_key = f"mf_{ticker}"
    cached = _read_cache(cache_key)
    if cached:
        return cached

    try:
        t = yf.Ticker(ticker)
        info = t.info
        bs = t.balance_sheet
    except Exception as e:
        print(f"  [!] Failed to fetch Magic Formula data for {ticker}: {e}")
        return None

    if bs is None or bs.empty:
        print(f"  [!] No balance sheet data for {ticker}")
        return None

    # Most recent quarter (first column)
    def bs_val(field):
        if field in bs.index:
            v = bs.iloc[bs.index.get_loc(field), 0]
            return _safe_float(v)
        return None

    # FCFF ≈ Operating Cash Flow - CapEx
    # yfinance's freeCashflow is already OCF - CapEx
    fcff = info.get("freeCashflow")

    # Invested Capital (Greenblatt) = Net Working Capital + Net Fixed Assets
    # Deliberately excludes goodwill and intangibles — that's the point
    working_capital = bs_val("Working Capital")  # Current Assets - Current Liabilities
    net_ppe = bs_val("Net PPE")

    invested_capital = None
    if working_capital is not None and net_ppe is not None:
        invested_capital = working_capital + net_ppe

    total_assets = bs_val("Total Assets")
    enterprise_value = info.get("enterpriseValue")

    data = {
        "ticker": ticker,
        "name": info.get("shortName") or info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "market_cap": info.get("marketCap"),
        "enterprise_value": enterprise_value,
        "fcff": fcff,
        "working_capital": working_capital,
        "net_ppe": net_ppe,
        "invested_capital_greenblatt": invested_capital,
        "total_assets": total_assets,
        # Pre-compute the three metrics
        "roic": _safe_div(fcff, invested_capital),
        "earnings_yield": _safe_div(fcff, enterprise_value),
        "roi": _safe_div(fcff, total_assets),
    }

    _write_cache(cache_key, data)
    return data


def _safe_div(a, b) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _safe_float(val) -> float | None:
    """Convert to float, handling None, 'Infinity', NaN, etc."""
    if val is None:
        return None
    try:
        f = float(val)
        if f != f or f == float("inf") or f == float("-inf"):
            return None
        return f
    except (ValueError, TypeError):
        return None
