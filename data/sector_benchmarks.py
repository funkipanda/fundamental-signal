"""
Damodaran sector benchmark loader.
Downloads P/E, P/B, EV/EBITDA by industry from NYU Stern Excel files.
Caches locally as JSON.
"""

import json
import sys
import time
from difflib import get_close_matches
from pathlib import Path

import pandas as pd

from config import BENCHMARK_CACHE_DAYS, INDUSTRY_MAP, SECTOR_FALLBACK

CACHE_DIR = Path(__file__).parent / "cache"

# Each file has sheet "Industry Averages" with metadata rows, then a header, then data.
# PE and PB: header at row 6 → skiprows=6
# EV/EBITDA: extra sub-header row → header at row 7 → skiprows=7
DAMODARAN_FILES = {
    "pe": {
        "url": "https://www.stern.nyu.edu/~adamodar/pc/datasets/pedata.xls",
        "skiprows": 7,
        "col": "Forward PE",           # Forward PE is less skewed than Current PE (simple avg)
        "col_fallback": "Current PE",
    },
    "pb": {
        "url": "https://www.stern.nyu.edu/~adamodar/pc/datasets/pbvdata.xls",
        "skiprows": 7,
        "col": "PBV",
        "col_fallback": None,
    },
    "ev_ebitda": {
        "url": "https://www.stern.nyu.edu/~adamodar/pc/datasets/vebitda.xls",
        "skiprows": 8,
        "col": "EV/EBITDA",
        "col_fallback": None,
    },
}


def load_sector_benchmarks(force_refresh: bool = False) -> dict:
    """
    Load Damodaran sector benchmarks.
    Returns dict: {damodaran_industry_name: {"pe": float, "pb": float, "ev_ebitda": float}}
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "damodaran_benchmarks.json"

    if cache_file.exists() and not force_refresh:
        age_days = (time.time() - cache_file.stat().st_mtime) / 86400
        if age_days < BENCHMARK_CACHE_DAYS:
            data = json.loads(cache_file.read_text())
            if data:  # Don't use empty cache
                return data

    print("[*] Downloading Damodaran sector benchmarks...")
    benchmarks = {}

    for metric_key, spec in DAMODARAN_FILES.items():
        try:
            df = pd.read_excel(
                spec["url"],
                sheet_name="Industry Averages",
                skiprows=spec["skiprows"],
                engine="xlrd",
            )

            # First column is "Industry Name"
            name_col = df.columns[0]
            value_col = _find_column(df, spec["col"])
            if value_col is None and spec.get("col_fallback"):
                value_col = _find_column(df, spec["col_fallback"])

            if value_col is None:
                # Fall back to column index 3 for PE (Current PE), 2 for PB/EV
                fallback_idx = 3 if metric_key == "pe" else 2
                if fallback_idx < len(df.columns):
                    value_col = df.columns[fallback_idx]

            count = 0
            for _, row in df.iterrows():
                name = _clean_industry_name(row[name_col])
                if not name:
                    continue
                val = _to_float(row[value_col]) if value_col is not None else None
                if val is not None:
                    if name not in benchmarks:
                        benchmarks[name] = {}
                    benchmarks[name][metric_key] = val
                    count += 1

            print(f"    {metric_key.upper()}: {count} industries loaded")

        except Exception as e:
            print(f"  [!] Failed to load {metric_key} data: {e}", file=sys.stderr)

    # Save cache
    if benchmarks:
        cache_file.write_text(json.dumps(benchmarks, indent=2))
        print(f"[*] Cached {len(benchmarks)} industry benchmarks\n")
    else:
        print("[!] No benchmarks loaded — will use sector fallbacks\n")

    return benchmarks


def get_benchmark(industry: str | None, sector: str | None, benchmarks: dict) -> dict:
    """
    Get benchmark multiples for a stock's industry.
    Tries: 1) INDUSTRY_MAP, 2) fuzzy match, 3) broad sector fallback.
    """
    result = {"pe": None, "pb": None, "ev_ebitda": None, "source": "none", "matched_name": None}

    if industry and benchmarks:
        # 1. Manual mapping
        damodaran_name = INDUSTRY_MAP.get(industry)
        if damodaran_name and damodaran_name in benchmarks:
            bench = benchmarks[damodaran_name]
            result.update({
                "pe": bench.get("pe"),
                "pb": bench.get("pb"),
                "ev_ebitda": bench.get("ev_ebitda"),
                "source": "damodaran_mapped",
                "matched_name": damodaran_name,
            })
            return result

        # 2. Fuzzy match against Damodaran industry names
        all_names = list(benchmarks.keys())
        matches = get_close_matches(industry, all_names, n=1, cutoff=0.5)
        if matches:
            match = matches[0]
            bench = benchmarks[match]
            result.update({
                "pe": bench.get("pe"),
                "pb": bench.get("pb"),
                "ev_ebitda": bench.get("ev_ebitda"),
                "source": "damodaran_fuzzy",
                "matched_name": match,
            })
            print(f"  [~] Fuzzy matched '{industry}' → '{match}'", file=sys.stderr)
            return result

    # 3. Broad sector fallback
    if sector and sector in SECTOR_FALLBACK:
        fb = SECTOR_FALLBACK[sector]
        result.update({
            "pe": fb.get("pe"),
            "pb": fb.get("pb"),
            "ev_ebitda": fb.get("ev_ebitda"),
            "source": "sector_fallback",
            "matched_name": sector,
        })
        return result

    return result


def _find_column(df: pd.DataFrame, target: str) -> str | None:
    """Find a column name that contains the target string (case-insensitive)."""
    target_lower = target.lower()
    for col in df.columns:
        if isinstance(col, str) and target_lower in col.lower():
            return col
    return None


def _clean_industry_name(val) -> str | None:
    if not isinstance(val, str):
        return None
    val = val.strip()
    if not val or len(val) < 3:
        return None
    lower = val.lower()
    if lower in ("total market", "total", "market", "grand total", "industry name"):
        return None
    return val


def _to_float(val) -> float | None:
    if val is None or (isinstance(val, float) and val != val):
        return None
    try:
        f = float(val)
        if f == float("inf") or f == float("-inf") or f < 0:
            return None
        if f > 500:
            return None  # Likely meaningless outlier for a multiple
        return round(f, 2)
    except (ValueError, TypeError):
        return None
