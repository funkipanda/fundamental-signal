"""
FastAPI backend for the Fundamental Signal screener.
Serves the frontend and exposes a /api/screen endpoint.
"""

import json
import time
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from analysis.magic_formula import rank_stocks
from analysis.scorer import classify_stock, compute_all_divergences, compute_metrics
from data.fetcher import fetch_magic_formula_data, fetch_with_fallback
from data.sector_benchmarks import get_benchmark, load_sector_benchmarks

app = FastAPI(title="Fundamental Signal")

DESIGN_DIR = Path(__file__).parent / "Fundamental Signal Design System (1)"

# Mount design system assets
app.mount("/assets", StaticFiles(directory=DESIGN_DIR / "assets"), name="assets")

# Load benchmarks once at startup
_benchmarks: dict = {}


@app.on_event("startup")
def startup():
    global _benchmarks
    _benchmarks = load_sector_benchmarks()


class ScreenRequest(BaseModel):
    tickers: list[str]


@app.get("/colors_and_type.css")
def serve_css():
    return FileResponse(DESIGN_DIR / "colors_and_type.css", media_type="text/css")


@app.get("/")
def serve_frontend():
    return FileResponse(Path(__file__).parent / "index.html", media_type="text/html")


@app.post("/api/screen")
def screen_tickers(req: ScreenRequest):
    """Screen tickers and return structured results for the frontend."""
    # Deduplicate, uppercase
    seen = set()
    tickers = []
    for t in req.tickers:
        t = t.strip().upper()
        if t and t not in seen:
            seen.add(t)
            tickers.append(t)

    results = []
    for i, ticker in enumerate(tickers):
        data = fetch_with_fallback(ticker)
        if data is None:
            results.append({"ticker": ticker, "error": "Failed to fetch data"})
            continue

        metrics = compute_metrics(data)
        sector_bench = get_benchmark(data.get("industry"), data.get("sector"), _benchmarks)
        divergences = compute_all_divergences(metrics, sector_bench)
        classification = classify_stock(data, metrics, divergences, sector_bench)

        # Build frontend-friendly response
        m = metrics
        de_suppressed = "ev_ebitda" in classification.get("suppressed_metrics", [])
        sector = data.get("sector", "")

        # Price range position
        low_52 = m.get("fifty_two_week_low")
        high_52 = m.get("fifty_two_week_high")
        price = m.get("current_price")

        results.append({
            "ticker": ticker,
            "name": data.get("name"),
            "sector": data.get("sector"),
            "industry": data.get("industry"),
            "classification": classification["classification"],
            "confidence": classification["confidence"],
            "price": price,
            "metrics": {
                "forward_pe": m.get("forward_pe"),
                "forward_pe_sector": sector_bench.get("pe"),
                "ev_ebitda": m.get("ev_ebitda"),
                "ev_ebitda_sector": sector_bench.get("ev_ebitda"),
                "suppressed_ev": de_suppressed,
                "fcf_yield": m.get("fcf_yield"),
                "suppressed_fcf": de_suppressed,  # Suppress FCF for financials too
                "roe": m.get("roe"),
                "cf_quality": m.get("cf_quality"),
                "debt_equity": m.get("debt_equity"),
                "suppressed_de": de_suppressed,
            },
            "range52": {
                "low": low_52,
                "high": high_52,
                "ma50": m.get("fifty_day_avg"),
                "ma200": m.get("two_hundred_day_avg"),
            },
            "flags": [
                {"kind": _flag_kind(f, classification["classification"]), "text": f}
                for f in classification.get("flags", [])
            ],
            "sectorNote": classification.get("sector_note"),
            "benchmarkSource": classification.get("benchmark_source"),
            "benchmarkMatch": classification.get("benchmark_match"),
        })

        # Rate limit between tickers
        if i < len(tickers) - 1:
            time.sleep(1.0)

    # Sort by signal priority
    order = {"UNDERVALUED": 0, "VALUE_TRAP": 1, "OVERVALUED": 2, "QUALITY_PREMIUM": 3, "FAIR_VALUE": 4}
    results.sort(key=lambda r: order.get(r.get("classification", ""), 5))

    return {"results": results, "count": len(results)}


@app.post("/api/magic-formula")
def magic_formula(req: ScreenRequest):
    """Rank tickers by FCFF-based Magic Formula (ROIC + Earnings Yield + ROI)."""
    seen = set()
    tickers = []
    for t in req.tickers:
        t = t.strip().upper()
        if t and t not in seen:
            seen.add(t)
            tickers.append(t)

    stocks = []
    for i, ticker in enumerate(tickers):
        data = fetch_magic_formula_data(ticker)
        if data:
            stocks.append(data)
        if i < len(tickers) - 1:
            time.sleep(1.0)

    results = rank_stocks(stocks)
    return {"results": results, "count": len(results), "ranked": sum(1 for r in results if not r.get("excluded"))}


@app.get("/api/sp500")
def get_sp500():
    """Fetch current S&P 500 tickers from Wikipedia. Cached locally for 7 days."""
    import io
    import requests as req

    cache_file = Path(__file__).parent / "data" / "cache" / "sp500.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    if cache_file.exists():
        age_days = (time.time() - cache_file.stat().st_mtime) / 86400
        if age_days < 7:
            return json.loads(cache_file.read_text())

    resp = req.get(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        headers={"User-Agent": "FundamentalSignal/1.0"},
    )
    tables = pd.read_html(io.StringIO(resp.text))
    df = tables[0]
    tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
    result = {"tickers": tickers, "count": len(tickers)}
    cache_file.write_text(json.dumps(result))
    return result


def _flag_kind(flag_text: str, classification: str) -> str:
    """Determine flag color kind from text content and classification."""
    text = flag_text.lower()
    if "warning" in text or "decline" in text or "leverage" in text:
        return "o"  # red
    if "cheap" in text or "discount" in text or "undervalued" in text:
        return "u"  # green
    if "trap" in text or "investigate" in text or "cyclical" in text:
        return "t"  # yellow
    if "premium" in text or "quality" in text or "strong" in text:
        return "p"  # blue
    # Default based on classification
    cls_map = {"UNDERVALUED": "u", "VALUE_TRAP": "t", "OVERVALUED": "o", "QUALITY_PREMIUM": "p", "FAIR_VALUE": "f"}
    return cls_map.get(classification, "f")
