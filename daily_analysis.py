"""
daily_analysis.py — Daily Trading Decision System
==================================================
Professional-grade pipeline:
  1. Read watchlist from watchlist.xlsx (add tickers daily)
  2. Fetch 3-year OHLCV (Yahoo Finance)
  3. Run 6-strategy confluence scanner
  4. Walk-forward backtest + Monte Carlo validation
  5. Position sizing (ATR-based, 1% risk per trade)
  6. Output: analysis_output.xlsx with full decision matrix

Recommendations:
  POSITIONAL LONG/SHORT — hold weeks, strong trend + 3+ signals
  SWING LONG/SHORT      — hold days, trending + 2+ signals
  SCALPING LONG/SHORT   — intraday, volume spike + tight range
  NO TRADE              — no edge or no confluence

USAGE:
    python daily_analysis.py                    # today's analysis
    python daily_analysis.py --date 2026-06-25  # specific date
    python daily_analysis.py --capital 200000   # custom capital for sizing
"""

import argparse
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).parent))
from engine.data import fetch_ohlcv
from engine.strategies import run_all_strategies
from engine.backtest import forward_sim, bootstrap_mc
from engine.recommendation import classify_trade, position_size

BASE_DIR = Path(__file__).parent
WATCHLIST_PATH = BASE_DIR / "watchlist.xlsx"
OUTPUT_PATH = BASE_DIR / "analysis_output.xlsx"


def read_watchlist():
    if not WATCHLIST_PATH.exists():
        print(f"Creating template watchlist at: {WATCHLIST_PATH}")
        template = pd.DataFrame({
            "ticker": ["RELIANCE", "HDFCBANK", "INFY", "TCS", "ITC",
                       "WIPRO", "SBIN", "MARUTI", "LT", "BHARTIARTL"],
            "date_added": [datetime.now().strftime("%Y-%m-%d")] * 10,
            "notes": [""] * 10,
        })
        template.to_excel(WATCHLIST_PATH, index=False, sheet_name="Watchlist")
        print("  -> Add your tickers to watchlist.xlsx and re-run.\n")
        return template
    return pd.read_excel(WATCHLIST_PATH, sheet_name="Watchlist")


def analyze_ticker(ticker, capital):
    df = fetch_ohlcv(ticker, years=3)
    if df is None:
        return None, "Insufficient data"

    signals = run_all_strategies(df)
    meta = signals["_meta"]

    # Backtest on out-of-sample (last 40%)
    cut = max(200, int(len(df) * 0.6))
    bt_df = df.iloc[cut - 200:]
    bt_result = forward_sim(bt_df)
    total_ret, max_dd, win_rate, trade_count, avg_hold, trades = bt_result

    mc = bootstrap_mc(trades)
    trade_type, confidence, reason, risk_notes = classify_trade(signals, bt_result, mc)

    # Position sizing
    shares, stop_loss = position_size(capital, meta["last_price"], meta["atr"])

    return {
        "ticker": ticker,
        "price": round(meta["last_price"], 2),
        "recommendation": trade_type,
        "confidence_%": confidence,
        "reason": reason,
        "risk_notes": risk_notes,
        # Position sizing
        "qty": shares,
        "stop_loss": stop_loss,
        "risk_amt": round(shares * (meta["atr"] or 0) * 2, 0) if shares else 0,
        # Signals
        "momentum": signals["momentum_sma"]["signal"],
        "ema18": signals["ema18_breakout"]["signal"],
        "impulse": signals["gold_impulse"]["signal"],
        "8020": signals["strategy_8020"]["signal"],
        "volume": signals["volume"]["signal"],
        "adx": signals["adx"]["signal"],
        # Context
        "regime": signals["adx"].get("regime", ""),
        "adx_val": signals["adx"].get("adx", ""),
        "vol_ratio": signals["volume"].get("vol_ratio", ""),
        "atr_%": meta["atr_pct"],
        # Backtest
        "bt_ret_%": round(total_ret, 1),
        "bt_dd_%": round(max_dd, 1),
        "bt_wr_%": round(win_rate, 0),
        "bt_trades": trade_count,
        "bt_avg_hold": round(avg_hold, 0),
        # Monte Carlo
        "mc_p5_%": mc["p5_return"] if mc else "",
        "mc_med_%": mc["median_return"] if mc else "",
        "mc_p95_%": mc["p95_return"] if mc else "",
        "mc_loss_prob_%": mc["p_loss"] if mc else "",
        "mc_worst_dd_%": mc["worst5_dd"] if mc else "",
    }, None


def write_output(results, analysis_date):
    df = pd.DataFrame(results)
    df.insert(0, "date", analysis_date)

    # Sort: high-confidence actionable first
    df["_sort"] = df["confidence_%"].apply(lambda x: -x if x > 0 else 999)
    df = df.sort_values("_sort").drop(columns=["_sort"])

    # Load existing history if file exists
    history = None
    if OUTPUT_PATH.exists():
        try:
            history = pd.read_excel(OUTPUT_PATH, sheet_name="History")
        except (ValueError, KeyError):
            pass

    # Append today's results to history
    history_row = df[["date", "ticker", "price", "recommendation", "confidence_%",
                      "regime", "bt_ret_%", "mc_loss_prob_%"]].copy()
    if history is not None:
        history = pd.concat([history, history_row], ignore_index=True)
    else:
        history = history_row

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Analysis")

        summary = df[["ticker", "price", "recommendation", "confidence_%",
                      "qty", "stop_loss", "reason", "regime", "bt_ret_%",
                      "mc_loss_prob_%"]].copy()
        summary.to_excel(writer, index=False, sheet_name="Summary")

        history.to_excel(writer, index=False, sheet_name="History")

        for sheet_name in ["Analysis", "Summary"]:
            ws = writer.sheets[sheet_name]
            sheet_df = df if sheet_name == "Analysis" else summary
            for col_idx, col in enumerate(sheet_df.columns, 1):
                max_len = max(len(str(col)), sheet_df[col].astype(str).str.len().max())
                ws.column_dimensions[ws.cell(1, col_idx).column_letter].width = min(max_len + 2, 22)

    return df


def main():
    parser = argparse.ArgumentParser(description="Daily Trading Analysis")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--capital", type=float, default=100000,
                        help="Capital for position sizing (default: 1L)")
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"  DAILY ANALYSIS - {args.date} - Capital: Rs {args.capital:,.0f}")
    print(f"{'='*60}\n")

    watchlist = read_watchlist()
    tickers = watchlist["ticker"].dropna().tolist()
    print(f"Scanning {len(tickers)} stocks...\n")

    results = []
    errors = []
    for ticker in tickers:
        ticker = ticker.strip().upper()
        print(f"  {ticker:<12}", end="")
        result, err = analyze_ticker(ticker, args.capital)
        if result:
            rec = result["recommendation"]
            conf = result["confidence_%"]
            print(f" -> {rec:<20} [{conf}%]")
            results.append(result)
        else:
            print(f" -> SKIP ({err})")
            errors.append(ticker)

    if not results:
        print("\nNo results. Check watchlist tickers.")
        return

    df = write_output(results, args.date)

    # Console summary
    actionable = [r for r in results if r["confidence_%"] > 0]
    print(f"\n{'='*60}")
    print(f"  RESULTS: {len(actionable)} actionable / {len(results)} analyzed")
    if errors:
        print(f"  SKIPPED: {', '.join(errors)}")
    print(f"{'='*60}")

    if actionable:
        print(f"\n  {'Ticker':<10} {'Action':<20} {'Conf':>4} {'Qty':>5} {'Stop':>8} {'Reason'}")
        print(f"  {'-'*10} {'-'*20} {'-'*4} {'-'*5} {'-'*8} {'-'*30}")
        for r in sorted(actionable, key=lambda x: -x["confidence_%"]):
            print(f"  {r['ticker']:<10} {r['recommendation']:<20} {r['confidence_%']:>3}% "
                  f"{r['qty']:>5} {r['stop_loss']:>8} {r['reason'][:40]}")

    print(f"\n  Output: {OUTPUT_PATH}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
