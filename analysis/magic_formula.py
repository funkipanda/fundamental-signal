"""
FCFF-based Magic Formula ranking.

Inspired by Joel Greenblatt's Magic Formula, but replaces EBIT with
Free Cash Flow to the Firm (FCFF = Operating Cash Flow - CapEx).

Two metrics, each ranked across the universe:
  1. ROIC          = FCFF / Invested Capital (NWC + Net PP&E, excludes goodwill)
  2. Earnings Yield = FCFF / Enterprise Value

Combined rank = sum of the two individual ranks (lower = better).
"""


def rank_stocks(stocks: list[dict]) -> list[dict]:
    """
    Takes a list of stock dicts from fetch_magic_formula_data(),
    computes individual ranks for each metric, and returns
    the list sorted by combined rank (best first).

    Stocks missing critical data are placed at the bottom.
    """
    rankable = []
    unrankable = []

    for s in stocks:
        roic = s.get("roic")
        ey = s.get("earnings_yield")
        fcff = s.get("fcff")

        sector = (s.get("sector") or "").lower()
        is_financial = "financial" in sector

        if fcff is not None and fcff > 0 and roic is not None and ey is not None and not is_financial:
            rankable.append(s)
        else:
            reason = []
            if fcff is None or fcff <= 0:
                reason.append("negative or missing FCFF")
            if roic is None:
                reason.append("missing invested capital")
            if ey is None:
                reason.append("missing enterprise value")
            if is_financial:
                reason.append("financial sector excluded (structural leverage)")
            s["exclude_reason"] = "; ".join(reason)
            unrankable.append(s)

    if not rankable:
        return [_format_result(s, None, None, None, None) for s in unrankable]

    _assign_rank(rankable, "roic", "roic_rank")
    _assign_rank(rankable, "earnings_yield", "ey_rank")

    for s in rankable:
        s["combined_rank"] = s["roic_rank"] + s["ey_rank"]

    rankable.sort(key=lambda s: s["combined_rank"])

    results = []
    for i, s in enumerate(rankable):
        results.append(_format_result(
            s,
            position=i + 1,
            total=len(rankable),
            roic_rank=s["roic_rank"],
            ey_rank=s["ey_rank"],
            combined_rank=s["combined_rank"],
        ))

    for s in unrankable:
        results.append(_format_result(s, None, None, None, None))

    return results


def _assign_rank(stocks: list[dict], metric_key: str, rank_key: str):
    """Rank stocks by a metric. Highest value = rank 1 (best)."""
    sorted_by = sorted(stocks, key=lambda s: s.get(metric_key, 0), reverse=True)
    for i, s in enumerate(sorted_by):
        s[rank_key] = i + 1


def _format_result(s: dict, position, total, roic_rank, ey_rank, combined_rank=None) -> dict:
    fcff = s.get("fcff")
    return {
        "ticker": s.get("ticker"),
        "name": s.get("name"),
        "sector": s.get("sector"),
        "industry": s.get("industry"),
        "price": s.get("current_price"),
        "market_cap": s.get("market_cap"),
        "enterprise_value": s.get("enterprise_value"),
        "fcff": fcff,
        "fcff_display": _fmt_billions(fcff),
        "invested_capital": s.get("invested_capital_greenblatt"),
        "invested_capital_display": _fmt_billions(s.get("invested_capital_greenblatt")),
        "roic": s.get("roic"),
        "earnings_yield": s.get("earnings_yield"),
        "roic_rank": roic_rank,
        "ey_rank": ey_rank,
        "combined_rank": combined_rank,
        "position": position,
        "total_ranked": total,
        "excluded": position is None,
        "exclude_reason": s.get("exclude_reason"),
    }


def _fmt_billions(val) -> str | None:
    if val is None:
        return None
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1e9:
        return f"{sign}${abs_val / 1e9:.1f}B"
    if abs_val >= 1e6:
        return f"{sign}${abs_val / 1e6:.0f}M"
    return f"{sign}${abs_val:,.0f}"
