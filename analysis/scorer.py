"""
Scoring engine: compute metrics, divergences, and composite classification.
"""

from config import (
    CHEAPNESS_METRICS,
    MAX_DEBT_TO_EQUITY,
    METRICS,
    MIN_CF_QUALITY,
    MIN_ROE,
    MODERATE_DIVERGENCE_PCT,
    SECTOR_OVERRIDES,
    STRONG_DIVERGENCE_PCT,
)


def compute_metrics(data: dict) -> dict:
    """
    Compute the 6 core metrics from raw fetched data.
    Returns dict with metric keys matching METRICS config.
    """
    market_cap = data.get("market_cap")
    fcf = data.get("free_cashflow")
    ocf = data.get("operating_cashflow")
    ni = data.get("net_income")

    # yfinance returns debt_to_equity as a percentage (e.g., 150 = 1.5x)
    raw_de = data.get("debt_to_equity")
    de_ratio = raw_de / 100.0 if raw_de is not None else None

    # FCF Yield = Free Cash Flow / Market Cap
    fcf_yield = None
    if fcf is not None and market_cap and market_cap > 0:
        fcf_yield = fcf / market_cap

    # CF Quality = Operating Cash Flow / Net Income
    cf_quality = None
    if ocf is not None and ni is not None and ni != 0:
        cf_quality = ocf / ni

    return {
        "forward_pe": data.get("forward_pe"),
        "trailing_pe": data.get("trailing_pe"),
        "ev_ebitda": data.get("ev_to_ebitda"),
        "fcf_yield": fcf_yield,
        "roe": data.get("roe"),
        "debt_equity": de_ratio,
        "cf_quality": cf_quality,
        # Pass-through for context
        "price_to_book": data.get("price_to_book"),
        "revenue_growth": data.get("revenue_growth"),
        "operating_margin": data.get("operating_margin"),
        "dividend_yield": data.get("dividend_yield"),
        "current_price": data.get("current_price"),
        "market_cap": market_cap,
        "fifty_two_week_high": data.get("fifty_two_week_high"),
        "fifty_two_week_low": data.get("fifty_two_week_low"),
        "fifty_day_avg": data.get("fifty_day_avg"),
        "two_hundred_day_avg": data.get("two_hundred_day_avg"),
        "beta": data.get("beta"),
    }


def compute_divergence(stock_value: float | None, sector_value: float | None, direction: str) -> dict:
    """
    Compute how far a stock's metric diverges from the sector benchmark.
    Returns: {pct_diff, signal, strength}
    """
    if stock_value is None or sector_value is None or sector_value == 0:
        return {"pct_diff": None, "signal": "no_data", "strength": None}

    pct_diff = (stock_value - sector_value) / abs(sector_value) * 100

    # For "lower is better" metrics, a negative pct_diff means cheaper (favorable)
    favorable_diff = -pct_diff if direction == "lower" else pct_diff

    if favorable_diff > STRONG_DIVERGENCE_PCT:
        return {"pct_diff": pct_diff, "signal": "undervalued", "strength": "strong"}
    elif favorable_diff > MODERATE_DIVERGENCE_PCT:
        return {"pct_diff": pct_diff, "signal": "undervalued", "strength": "moderate"}
    elif favorable_diff < -STRONG_DIVERGENCE_PCT:
        return {"pct_diff": pct_diff, "signal": "overvalued", "strength": "strong"}
    elif favorable_diff < -MODERATE_DIVERGENCE_PCT:
        return {"pct_diff": pct_diff, "signal": "overvalued", "strength": "moderate"}
    else:
        return {"pct_diff": pct_diff, "signal": "neutral", "strength": "weak"}


def compute_all_divergences(metrics: dict, sector_bench: dict) -> dict:
    """Compute divergences for the 3 cheapness metrics against sector benchmarks."""
    bench_map = {
        "forward_pe": sector_bench.get("pe"),
        "ev_ebitda": sector_bench.get("ev_ebitda"),
        "fcf_yield": 0.05,  # 5% as baseline — Damodaran doesn't provide FCF yield by sector
    }

    divergences = {}
    for key in CHEAPNESS_METRICS:
        meta = METRICS[key]
        stock_val = metrics.get(key)
        bench_val = bench_map.get(key)
        divergences[key] = compute_divergence(stock_val, bench_val, meta["direction"])

    return divergences


def classify_stock(data: dict, metrics: dict, divergences: dict, sector_bench: dict) -> dict:
    """
    Apply composite classification logic.
    Returns: {classification, confidence, flags, sector_note}
    """
    sector = data.get("sector", "")
    overrides = SECTOR_OVERRIDES.get(sector, {})
    suppressed = overrides.get("suppress", [])
    flags = []

    # --- Count cheapness/expensiveness signals ---
    active_cheap_metrics = [m for m in CHEAPNESS_METRICS if m not in suppressed]

    cheap_count = 0
    expensive_count = 0
    for m in active_cheap_metrics:
        sig = divergences.get(m, {}).get("signal", "no_data")
        if sig == "undervalued":
            cheap_count += 1
        elif sig == "overvalued":
            expensive_count += 1

    # --- Quality checks ---
    roe = metrics.get("roe")
    cf_quality = metrics.get("cf_quality")
    de_ratio = metrics.get("debt_equity")

    de_threshold = overrides.get("de_threshold", MAX_DEBT_TO_EQUITY)

    quality_pass = True
    quality_issues = []

    if roe is not None and roe < MIN_ROE:
        quality_pass = False
        quality_issues.append(f"ROE is {roe:.1%} (below {MIN_ROE:.0%} threshold)")

    if cf_quality is not None and cf_quality < MIN_CF_QUALITY:
        quality_pass = False
        quality_issues.append(f"CF Quality is {cf_quality:.1f}x (below {MIN_CF_QUALITY}x — earnings may not be backed by cash)")

    health_pass = True
    if de_threshold is not None and de_ratio is not None and de_ratio > de_threshold:
        health_pass = False
        flags.append(f"LEVERAGE WARNING: D/E ratio is {de_ratio:.1f}x (above {de_threshold:.1f}x)")

    # --- Classification ---
    active_count = len(active_cheap_metrics)
    min_signals = 2 if active_count >= 3 else 1

    if cheap_count >= min_signals and quality_pass and health_pass:
        classification = "UNDERVALUED"
        confidence = "high" if cheap_count == active_count else "medium"
        flags.insert(0, f"Trading at a discount to sector on {cheap_count}/{active_count} valuation metrics")
        if roe is not None:
            flags.append(f"Quality filters pass: ROE {roe:.1%}")
        if cf_quality is not None:
            flags.append(f"Cash flow quality: {cf_quality:.1f}x (earnings backed by cash)")

    elif cheap_count >= min_signals and not quality_pass:
        classification = "VALUE_TRAP"
        confidence = "medium"
        flags.insert(0, f"Looks cheap on {cheap_count}/{active_count} valuation metrics — but quality concerns:")
        for issue in quality_issues:
            flags.append(f"  WARNING: {issue}")
        flags.append("Cheap for a reason? Investigate before buying.")

    elif expensive_count >= min_signals and quality_pass:
        classification = "QUALITY_PREMIUM"
        confidence = "medium"
        flags.insert(0, f"Trading at a premium to sector on {expensive_count}/{active_count} valuation metrics")
        if roe is not None:
            flags.append(f"Quality is strong: ROE {roe:.1%} — market may be pricing in growth")

    elif expensive_count >= min_signals and not quality_pass:
        classification = "OVERVALUED"
        confidence = "high" if expensive_count == active_count else "medium"
        flags.insert(0, f"Expensive on {expensive_count}/{active_count} valuation metrics with deteriorating quality")
        for issue in quality_issues:
            flags.append(f"  {issue}")

    else:
        classification = "FAIR_VALUE"
        confidence = "low"
        flags.insert(0, "No strong valuation divergence — trading near sector norms")

    # --- Additional contextual flags ---
    rev_growth = metrics.get("revenue_growth")
    if rev_growth is not None and rev_growth < -0.05:
        flags.append(f"REVENUE DECLINE: {rev_growth:.1%} YoY — investigate if structural")

    price = metrics.get("current_price")
    low_52 = metrics.get("fifty_two_week_low")
    high_52 = metrics.get("fifty_two_week_high")
    if price and low_52 and high_52 and (high_52 - low_52) > 0:
        position = (price - low_52) / (high_52 - low_52)
        if position < 0.2:
            flags.append("NEAR 52-WEEK LOW: trading in bottom 20% of range")
        elif position > 0.9:
            flags.append("NEAR 52-WEEK HIGH: trading in top 10% of range")

    # Cyclicality warning
    if overrides.get("cyclicality_warning"):
        flags.append(f"CYCLICAL SECTOR: {overrides.get('note', '')}")

    sector_note = overrides.get("note")

    return {
        "classification": classification,
        "confidence": confidence,
        "flags": flags,
        "sector_note": sector_note,
        "suppressed_metrics": suppressed,
        "benchmark_source": sector_bench.get("source", "none"),
        "benchmark_match": sector_bench.get("matched_name"),
    }
