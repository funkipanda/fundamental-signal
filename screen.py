#!/usr/bin/env python3
"""
Price vs. Fundamentals Discrepancy Screener

Usage:
    python screen.py AAPL MSFT GOOGL          # Screen specific tickers
    python screen.py --watchlist watch.txt      # Screen tickers from a file
    python screen.py AAPL --output md           # Also write markdown report
    python screen.py --refresh-benchmarks       # Force re-download Damodaran data
"""

import argparse
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from analysis.scorer import classify_stock, compute_all_divergences, compute_metrics
from data.fetcher import fetch_with_fallback
from data.sector_benchmarks import get_benchmark, load_sector_benchmarks
from output.report import console, print_detail_cards, print_summary_table, write_markdown_report


def main():
    parser = argparse.ArgumentParser(
        description="Screen stocks for price vs. fundamentals discrepancies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("tickers", nargs="*", help="Stock tickers to screen (e.g., AAPL MSFT JPM)")
    parser.add_argument("--watchlist", type=Path, help="File with tickers, one per line")
    parser.add_argument("--output", choices=["terminal", "md", "both"], default="terminal",
                        help="Output format (default: terminal)")
    parser.add_argument("--refresh-benchmarks", action="store_true",
                        help="Force re-download of Damodaran sector benchmarks")

    args = parser.parse_args()

    # Collect tickers
    tickers = [t.strip().upper() for t in args.tickers]
    if args.watchlist:
        if not args.watchlist.exists():
            console.print(f"[red]Error: watchlist file not found: {args.watchlist}[/red]")
            sys.exit(1)
        tickers.extend(
            line.strip().upper()
            for line in args.watchlist.read_text().strip().split("\n")
            if line.strip() and not line.strip().startswith("#")
        )

    if not tickers:
        parser.error("Provide at least one ticker or --watchlist file")

    # Deduplicate, preserve order
    seen = set()
    unique_tickers = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            unique_tickers.append(t)
    tickers = unique_tickers

    console.print(f"\n[bold]Screening {len(tickers)} ticker(s)...[/bold]\n")

    # 1. Load sector benchmarks
    benchmarks = load_sector_benchmarks(force_refresh=args.refresh_benchmarks)
    if not benchmarks:
        console.print("[yellow]Warning: Damodaran benchmarks unavailable. Using sector fallbacks only.[/yellow]\n")

    # 2. Fetch data for each ticker
    console.print("[dim]Fetching stock data...[/dim]")
    stock_data = []
    for i, ticker in enumerate(tickers):
        console.print(f"  [{i + 1}/{len(tickers)}] {ticker}...", end=" ")
        data = fetch_with_fallback(ticker)
        if data:
            console.print("[green]OK[/green]")
            stock_data.append(data)
        else:
            console.print("[red]FAILED[/red]")
        if i < len(tickers) - 1:
            time.sleep(1.5)

    if not stock_data:
        console.print("\n[red]No data retrieved for any ticker. Check your internet connection.[/red]")
        sys.exit(1)

    console.print(f"\n[dim]Retrieved data for {len(stock_data)}/{len(tickers)} tickers[/dim]\n")

    # 3. Score each stock
    results = []
    for data in stock_data:
        metrics = compute_metrics(data)
        sector_bench = get_benchmark(data.get("industry"), data.get("sector"), benchmarks)
        divergences = compute_all_divergences(metrics, sector_bench)
        classification = classify_stock(data, metrics, divergences, sector_bench)
        results.append({
            "data": data,
            "metrics": metrics,
            "sector_bench": sector_bench,
            "divergences": divergences,
            "classification": classification,
        })

    # Sort: most interesting signals first
    signal_order = {"UNDERVALUED": 0, "VALUE_TRAP": 1, "OVERVALUED": 2, "QUALITY_PREMIUM": 3, "FAIR_VALUE": 4}
    results.sort(key=lambda r: signal_order.get(r["classification"]["classification"], 5))

    # 4. Output
    print_summary_table(results)
    print_detail_cards(results)

    if args.output in ("md", "both"):
        write_markdown_report(results)

    # Quick stats
    counts = {}
    for r in results:
        c = r["classification"]["classification"]
        counts[c] = counts.get(c, 0) + 1
    stats = " | ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
    console.print(f"[dim]Summary: {stats}[/dim]\n")


if __name__ == "__main__":
    main()
