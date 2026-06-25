"""
Walk-forward backtest + Monte Carlo bootstrap.
Identical logic to batch_test.py / forward_and_montecarlo.py
but as a callable module with no side effects.
"""

import numpy as np
import pandas as pd
from .indicators import rsi


COSTS_PER_SIDE = 0.001 + 0.0000345 + 0.18 * 0.0000345 + 0.00015 + 0.000001 + 0.0015


def forward_sim(df, warmup=200, rsi_entry=10, capital=100000):
    """
    Walk-forward RSI-2 mean-reversion simulation.
    Returns: (total_return_pct, max_dd_pct, win_rate_pct, trade_count, avg_hold_days, trades_list)
    """
    closes = df["Close"].values
    c = COSTS_PER_SIDE
    cash, shares, in_pos, entry_price, entry_idx = capital, 0, False, 0.0, 0
    trades = []
    equities = []

    for i in range(warmup, len(closes)):
        window = closes[:i + 1]
        price = window[-1]
        sma_long = window[-200:].mean()
        sma_exit = window[-5:].mean()
        rsi_val = rsi(window)[-1] if len(window) > 2 else 50

        if not in_pos:
            if rsi_val < rsi_entry and price > sma_long:
                shares = int(cash // (price * (1 + c)))
                if shares > 0:
                    cash -= shares * price * (1 + c)
                    in_pos, entry_price, entry_idx = True, price, i
        else:
            if price > sma_exit:
                cash += shares * price * (1 - c)
                trades.append({
                    "ret_pct": (price / entry_price - 1) * 100,
                    "held_days": i - entry_idx,
                })
                shares, in_pos = 0, False

        equities.append(cash + shares * price)

    eq = np.array(equities)
    if len(eq) == 0:
        return 0, 0, 0, 0, 0, []

    total_ret = (eq[-1] / capital - 1) * 100
    peak = np.maximum.accumulate(eq)
    max_dd = ((eq - peak) / peak).min() * 100
    rets = [t["ret_pct"] for t in trades]
    win_rate = (np.array(rets) > 0).mean() * 100 if rets else 0
    avg_hold = np.mean([t["held_days"] for t in trades]) if trades else 0

    return total_ret, max_dd, win_rate, len(trades), avg_hold, trades


def bootstrap_mc(trades, n_sims=3000, capital=100000):
    """
    Bootstrap Monte Carlo on trade returns.
    Returns dict with percentiles or None if too few trades.
    """
    rets = [t["ret_pct"] for t in trades]
    if len(rets) < 3:
        return None

    rng = np.random.default_rng(42)
    r = np.array(rets) / 100
    k = len(r)

    finals = np.zeros(n_sims)
    dds = np.zeros(n_sims)

    for s in range(n_sims):
        sample = r[rng.integers(0, k, k)]
        eq = np.insert(capital * np.cumprod(1 + sample), 0, capital)
        finals[s] = (eq[-1] / capital - 1) * 100
        peak = np.maximum.accumulate(eq)
        dds[s] = ((eq - peak) / peak).min() * 100

    return {
        "p5_return": round(np.percentile(finals, 5), 1),
        "median_return": round(np.median(finals), 1),
        "p95_return": round(np.percentile(finals, 95), 1),
        "p_loss": round((finals < 0).mean() * 100, 1),
        "worst5_dd": round(np.percentile(dds, 5), 1),
        "median_dd": round(np.median(dds), 1),
    }
