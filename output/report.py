"""
Report formatter: Rich terminal output + optional markdown export.
"""

from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config import METRICS

console = Console()

CLASSIFICATION_COLORS = {
    "UNDERVALUED": "bold green",
    "VALUE_TRAP": "bold yellow",
    "OVERVALUED": "bold red",
    "QUALITY_PREMIUM": "bold cyan",
    "FAIR_VALUE": "dim",
}

CLASSIFICATION_ICONS = {
    "UNDERVALUED": "[green]▼ UNDERVALUED[/green]",
    "VALUE_TRAP": "[yellow]⚠ VALUE TRAP[/yellow]",
    "OVERVALUED": "[red]▲ OVERVALUED[/red]",
    "QUALITY_PREMIUM": "[cyan]★ QUALITY PREMIUM[/cyan]",
    "FAIR_VALUE": "[dim]― FAIR VALUE[/dim]",
}


def print_summary_table(results: list):
    """Print the main summary table for all screened tickers."""
    table = Table(
        title=f"PRICE vs. FUNDAMENTALS SCREEN — {datetime.now().strftime('%Y-%m-%d')}",
        title_style="bold white",
        show_lines=True,
        padding=(0, 1),
    )

    table.add_column("Ticker", style="bold", width=8)
    table.add_column("Name", width=22, overflow="ellipsis")
    table.add_column("Signal", width=18)
    table.add_column("Conf.", width=6)
    table.add_column("Fwd P/E\n(sector)", justify="right", width=12)
    table.add_column("EV/EBITDA\n(sector)", justify="right", width=12)
    table.add_column("FCF Yld", justify="right", width=8)
    table.add_column("ROE", justify="right", width=8)
    table.add_column("D/E", justify="right", width=6)

    for r in results:
        data = r["data"]
        metrics = r["metrics"]
        cls = r["classification"]
        divs = r["divergences"]

        cls_label = CLASSIFICATION_ICONS.get(cls["classification"], cls["classification"])
        conf = cls["confidence"]

        # Format metric cells with sector comparison
        fwd_pe = _fmt_vs_sector(metrics.get("forward_pe"), r["sector_bench"].get("pe"), "lower")
        ev_eb = _fmt_vs_sector(metrics.get("ev_ebitda"), r["sector_bench"].get("ev_ebitda"), "lower")
        fcf_y = _fmt_pct(metrics.get("fcf_yield"))
        roe = _fmt_pct(metrics.get("roe"))
        de = _fmt_ratio(metrics.get("debt_equity"))

        table.add_row(
            data.get("ticker", "?"),
            (data.get("name") or "")[:22],
            cls_label,
            conf,
            fwd_pe,
            ev_eb,
            fcf_y,
            roe,
            de,
        )

    console.print()
    console.print(table)
    console.print()


def print_detail_cards(results: list):
    """Print detailed cards for non-FAIR_VALUE results."""
    interesting = [r for r in results if r["classification"]["classification"] != "FAIR_VALUE"]
    if not interesting:
        console.print("[dim]No significant divergences detected.[/dim]\n")
        return

    for r in interesting:
        _print_card(r)


def _print_card(r: dict):
    data = r["data"]
    metrics = r["metrics"]
    cls = r["classification"]
    divs = r["divergences"]
    bench = r["sector_bench"]

    ticker = data.get("ticker", "?")
    name = data.get("name", "")
    sector = data.get("sector", "N/A")
    industry = data.get("industry", "N/A")
    price = metrics.get("current_price")
    mcap = metrics.get("market_cap")

    # Header
    header = f"{ticker} — {name}"
    sub = f"Sector: {sector} | Industry: {industry}"
    if price:
        sub += f"\nPrice: ${price:,.2f}"
    if mcap:
        sub += f" | Market Cap: ${mcap / 1e9:,.1f}B" if mcap > 1e9 else f" | Market Cap: ${mcap / 1e6:,.0f}M"

    # Classification line
    cls_name = cls["classification"]
    cls_color = CLASSIFICATION_COLORS.get(cls_name, "white")
    cls_line = f"[{cls_color}]{cls_name}[/{cls_color}] ({cls['confidence']} confidence)"
    if cls.get("benchmark_match"):
        cls_line += f"\nBenchmark: {cls['benchmark_match']} ({cls['benchmark_source']})"

    # Valuation vs sector
    val_lines = []
    for key in ["forward_pe", "ev_ebitda", "fcf_yield"]:
        meta = METRICS[key]
        stock_val = metrics.get(key)
        div = divs.get(key, {})
        suppressed = key in cls.get("suppressed_metrics", [])

        if suppressed:
            val_lines.append(f"  {meta['label']:12s}  N/A (suppressed for this sector)")
            continue

        if stock_val is None:
            val_lines.append(f"  {meta['label']:12s}  N/A")
            continue

        # Format the stock value
        if "%" in meta["format"]:
            stock_str = f"{stock_val:.1%}"
        else:
            stock_str = f"{stock_val:{meta['format']}}{meta['suffix']}"

        # Sector comparison
        bench_key = {"forward_pe": "pe", "ev_ebitda": "ev_ebitda", "fcf_yield": None}[key]
        bench_val = bench.get(bench_key) if bench_key else 0.05
        if bench_val:
            if bench_key:
                bench_str = f"{bench_val:.1f}{meta['suffix']}"
            else:
                bench_str = f"{bench_val:.1%}"
            pct = div.get("pct_diff")
            arrow = ""
            if pct is not None:
                if div["signal"] == "undervalued":
                    arrow = " [green]▼ cheap[/green]"
                elif div["signal"] == "overvalued":
                    arrow = " [red]▲ expensive[/red]"
            val_lines.append(f"  {meta['label']:12s}  {stock_str:>8s}  vs  {bench_str:>8s} sector{arrow}")
        else:
            val_lines.append(f"  {meta['label']:12s}  {stock_str:>8s}")

    # Quality section
    qual_lines = []
    roe = metrics.get("roe")
    cf_q = metrics.get("cf_quality")
    de = metrics.get("debt_equity")
    if roe is not None:
        check = "[green]✓[/green]" if roe >= 0.10 else "[red]✗[/red]"
        qual_lines.append(f"  ROE          {roe:>7.1%}  {check}")
    if cf_q is not None:
        check = "[green]✓[/green]" if cf_q >= 0.8 else "[red]✗[/red]"
        qual_lines.append(f"  CF Quality   {cf_q:>7.1f}x {check}")
    if de is not None:
        de_ok = cls.get("suppressed_metrics", [])
        if "ev_ebitda" in cls.get("suppressed_metrics", []):
            # Financial sector — don't judge D/E
            qual_lines.append(f"  D/E Ratio    {de:>7.1f}x (not applicable for this sector)")
        else:
            check = "[green]✓[/green]" if de <= 2.0 else "[red]✗[/red]"
            qual_lines.append(f"  D/E Ratio    {de:>7.1f}x {check}")

    # Price context
    price_lines = []
    low_52 = metrics.get("fifty_two_week_low")
    high_52 = metrics.get("fifty_two_week_high")
    if price and low_52 and high_52:
        price_lines.append(f"  52-wk range: ${low_52:,.2f} — ${high_52:,.2f}")
        if (high_52 - low_52) > 0:
            pct_pos = (price - low_52) / (high_52 - low_52) * 100
            price_lines.append(f"  Position in range: {pct_pos:.0f}%")
    avg_50 = metrics.get("fifty_day_avg")
    avg_200 = metrics.get("two_hundred_day_avg")
    if avg_50:
        price_lines.append(f"  50-day avg: ${avg_50:,.2f}")
    if avg_200:
        price_lines.append(f"  200-day avg: ${avg_200:,.2f}")
    beta = metrics.get("beta")
    if beta:
        price_lines.append(f"  Beta: {beta:.2f}")

    # Assemble body
    body = f"{sub}\n\n{cls_line}\n"
    body += "\n[bold]Valuation vs. Sector:[/bold]\n" + "\n".join(val_lines)
    body += "\n\n[bold]Quality:[/bold]\n" + "\n".join(qual_lines)
    if price_lines:
        body += "\n\n[bold]Price Context:[/bold]\n" + "\n".join(price_lines)
    body += "\n\n[bold]Flags:[/bold]"
    for flag in cls.get("flags", []):
        body += f"\n  • {flag}"
    if cls.get("sector_note"):
        body += f"\n\n[dim]Sector note: {cls['sector_note']}[/dim]"

    color = CLASSIFICATION_COLORS.get(cls_name, "white")
    console.print(Panel(body, title=f"[bold]{header}[/bold]", border_style=color, padding=(1, 2)))
    console.print()


def write_markdown_report(results: list, output_dir: Path | None = None):
    """Write results to a markdown file."""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = output_dir / f"{date_str}_screener.md"

    lines = [
        f"# Price vs. Fundamentals Screen — {date_str}\n",
        "",
        "## Summary\n",
        "| Ticker | Name | Signal | Confidence | Fwd P/E (sector) | EV/EBITDA (sector) | FCF Yield | ROE | D/E |",
        "|--------|------|--------|------------|-------------------|---------------------|-----------|-----|-----|",
    ]

    for r in results:
        data = r["data"]
        metrics = r["metrics"]
        cls = r["classification"]
        bench = r["sector_bench"]

        fpe = _md_vs(metrics.get("forward_pe"), bench.get("pe"), ".1f")
        eveb = _md_vs(metrics.get("ev_ebitda"), bench.get("ev_ebitda"), ".1f")
        fcfy = f"{metrics['fcf_yield']:.1%}" if metrics.get("fcf_yield") is not None else "N/A"
        roe = f"{metrics['roe']:.1%}" if metrics.get("roe") is not None else "N/A"
        de = f"{metrics['debt_equity']:.1f}x" if metrics.get("debt_equity") is not None else "N/A"

        lines.append(
            f"| {data.get('ticker', '?')} | {(data.get('name') or '')[:20]} | "
            f"**{cls['classification']}** | {cls['confidence']} | "
            f"{fpe} | {eveb} | {fcfy} | {roe} | {de} |"
        )

    lines.append("")
    lines.append("---\n")
    lines.append("## Detail Cards\n")

    for r in results:
        if r["classification"]["classification"] == "FAIR_VALUE":
            continue
        data = r["data"]
        metrics = r["metrics"]
        cls = r["classification"]

        lines.append(f"### {data.get('ticker', '?')} — {data.get('name', '')}")
        lines.append(f"**{cls['classification']}** ({cls['confidence']} confidence)\n")
        lines.append(f"Sector: {data.get('sector', 'N/A')} | Industry: {data.get('industry', 'N/A')}")
        price = metrics.get("current_price")
        if price:
            lines.append(f"Price: ${price:,.2f}")
        lines.append("")
        for flag in cls.get("flags", []):
            lines.append(f"- {flag}")
        if cls.get("sector_note"):
            lines.append(f"\n> *Sector note: {cls['sector_note']}*")
        lines.append("")

    filepath.write_text("\n".join(lines))
    console.print(f"[dim]Report written to {filepath}[/dim]\n")


# === Helpers ===

def _fmt_vs_sector(stock_val, sector_val, direction: str) -> str:
    if stock_val is None:
        return "N/A"
    s = f"{stock_val:.1f}"
    if sector_val is not None:
        s += f" ({sector_val:.0f})"
    return s


def _fmt_pct(val) -> str:
    if val is None:
        return "N/A"
    return f"{val:.1%}"


def _fmt_ratio(val) -> str:
    if val is None:
        return "N/A"
    return f"{val:.1f}x"


def _md_vs(stock_val, sector_val, fmt: str) -> str:
    if stock_val is None:
        return "N/A"
    s = f"{stock_val:{fmt}}"
    if sector_val is not None:
        s += f" ({sector_val:.0f})"
    return s
