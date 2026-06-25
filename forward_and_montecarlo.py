"""
forward_and_montecarlo.py
=========================

TWO honest tools that fit your existing RSI-2 mean-reversion system:

  A) FORWARD SIMULATOR (paper trading, done right)
     Walks the strategy DAY BY DAY through history. On each day it only
     knows "today and earlier" — never the future. Logs every paper
     trade as if you'd actually placed it (after costs). This is the
     bridge between "backtest looked ok" and "I'd risk money on it".
     NO broker. NO real orders. NO fake live dashboard.

  B) MONTE CARLO on STRATEGY TRADES (the useful kind)
     Takes the list of trade returns the strategy produced and reshuffles
     their ORDER thousands of times. Same trades, different sequence.
     Shows how bad the drawdown COULD have been with unlucky ordering.
     This is risk sizing, not prediction.

     NOT Monte Carlo on raw prices (the flashy, near-useless kind that
     just echoes back whatever random-walk assumption you feed it).

Data: synthetic here (Yahoo blocked in this sandbox). Swap get_data()
for the yfinance loader on your own machine — logic is identical.
"""

import numpy as np
import pandas as pd


# ---- reuse the same building blocks as the backtester -----------------
def make_synthetic(n_days=1500, seed=7):
    rng = np.random.default_rng(seed)
    trend = np.cumsum(np.full(n_days, 0.0003))
    mr = np.zeros(n_days)
    theta, sigma = 0.15, 0.012
    for t in range(1, n_days):
        mr[t] = mr[t-1] * (1 - theta) + rng.normal(0, sigma)
    price = np.exp(4.6 + trend + mr)
    return pd.DataFrame({"Close": price}, index=pd.bdate_range("2018-01-01", periods=n_days))

import yfinance as yf
def get_data():
    df = yf.download("RELIANCE.NS", start="2018-01-01",
                     end="2024-12-31", progress=False)
    df = df[["Close"]].dropna()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel("Ticker")
    return df

def rsi(series, period=2):
    delta = series.diff()
    gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1/period, adjust=False).mean()
    al = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = ag / al.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def cost_fraction_per_side():
    return 0.001 + 0.0000345 + 0.18*0.0000345 + 0.00015 + 0.000001 + 0.0015


# ======================================================================
# A) FORWARD SIMULATOR  — walk forward, one day at a time, no peeking
# ======================================================================
def forward_simulate(raw, warmup=200, rsi_entry=10, capital=50000, verbose=True):
    """
    Simulate trading the RSI-2 rule forward. On day i we compute indicators
    using ONLY data up to day i, decide, and (paper-)trade at day i's close.
    This mimics what you'd actually experience trading it live, but on paper.
    """
    c = cost_fraction_per_side()
    closes = raw["Close"]
    dates = raw.index

    cash, shares, in_pos, entry_price, entry_date = capital, 0, False, 0.0, None
    trades, equity = [], []

    for i in range(warmup, len(raw)):
        # --- only data up to and including today is visible ---
        window = closes.iloc[:i+1]
        price_today = window.iloc[-1]
        sma_long = window.tail(200).mean()
        sma_exit = window.tail(5).mean()
        rsi_today = rsi(window).iloc[-1]

        if not in_pos:
            if rsi_today < rsi_entry and price_today > sma_long:
                shares = int(cash // (price_today * (1 + c)))
                if shares > 0:
                    cash -= shares * price_today * (1 + c)
                    in_pos, entry_price, entry_date = True, price_today, dates[i]
        else:
            if price_today > sma_exit:
                cash += shares * price_today * (1 - c)
                trades.append({
                    "entry_date": entry_date, "exit_date": dates[i],
                    "entry": round(entry_price, 2), "exit": round(price_today, 2),
                    "ret_pct": round((price_today/entry_price - 1)*100, 2),
                    "held_days": (dates[i] - entry_date).days
                })
                shares, in_pos = 0, False

        equity.append({"date": dates[i], "equity": cash + shares * price_today})

    eq = pd.DataFrame(equity).set_index("date")["equity"]
    tr = pd.DataFrame(trades)

    if verbose:
        total = (eq.iloc[-1]/capital - 1)*100
        dd = ((eq - eq.cummax())/eq.cummax()).min()*100
        win = (tr["ret_pct"] > 0).mean()*100 if len(tr) else 0
        print("FORWARD SIMULATION (paper, walk-forward, no look-ahead)")
        print(f"  Period       : {eq.index[0].date()} to {eq.index[-1].date()}")
        print(f"  Final equity : Rs {eq.iloc[-1]:,.0f}  (start {capital:,.0f})")
        print(f"  Total return : {total:7.2f}%")
        print(f"  Max drawdown : {dd:7.2f}%")
        print(f"  Paper trades : {len(tr)}")
        print(f"  Win rate     : {win:7.1f}%")
    return eq, tr


# ======================================================================
# B) MONTE CARLO on the TRADES the strategy actually produced
# ======================================================================
def monte_carlo_trades(trade_returns_pct, n_sims=5000, capital=50000, seed=1):
    """
    trade_returns_pct: list/Series of per-trade % returns (e.g. tr['ret_pct']).

    TWO distinct simulations, because they answer two different questions:

    1. RESHUFFLE (permute order, no replacement):
       Same trades, different sequence. Final RETURN is identical every
       time (multiplication is commutative), so this tells us NOTHING about
       the return distribution -- but it DOES vary the drawdown path, so it
       is the right tool for "how bad could the drawdown have been by luck".

    2. BOOTSTRAP (resample WITH replacement):
       Draws a new set of trades from the same distribution. This varies
       WHICH trades happen and how many winners cluster, so it produces a
       real spread of final returns -- the right tool for "how uncertain
       is the return itself, given my sample is small".

    Using only #1 (the common mistake, which I made first) makes it look
    like the return is certain. It isn't.
    """
    rng = np.random.default_rng(seed)
    r = np.array(trade_returns_pct, dtype=float) / 100.0
    n = len(r)
    if n < 2:
        print("Not enough trades for Monte Carlo.")
        return None

    # --- 1. Reshuffle: drawdown path risk ---
    reshuffle_dds = []
    for _ in range(n_sims):
        eq = np.insert(capital * np.cumprod(1 + r[rng.permutation(n)]), 0, capital)
        peak = np.maximum.accumulate(eq)
        reshuffle_dds.append(((eq - peak)/peak).min() * 100)
    reshuffle_dds = np.array(reshuffle_dds)

    # --- 2. Bootstrap: return distribution (resample with replacement) ---
    boot_rets, boot_dds = [], []
    for _ in range(n_sims):
        sample = r[rng.integers(0, n, size=n)]
        eq = np.insert(capital * np.cumprod(1 + sample), 0, capital)
        boot_rets.append((eq[-1]/capital - 1) * 100)
        peak = np.maximum.accumulate(eq)
        boot_dds.append(((eq - peak)/peak).min() * 100)
    boot_rets = np.array(boot_rets); boot_dds = np.array(boot_dds)

    print(f"\nMONTE CARLO on {n} trades, {n_sims:,} sims each")
    print("  [Reshuffle - drawdown path risk, same trades reordered]")
    print(f"    Max DD : median {np.median(reshuffle_dds):6.2f}% | "
          f"worst 5% {np.percentile(reshuffle_dds,5):6.2f}% or deeper")
    print("  [Bootstrap - return uncertainty, trades resampled]")
    print(f"    Return : median {np.median(boot_rets):6.2f}% | "
          f"5th {np.percentile(boot_rets,5):6.2f}% | "
          f"95th {np.percentile(boot_rets,95):6.2f}%")
    print(f"    Max DD : median {np.median(boot_dds):6.2f}% | "
          f"worst 5% {np.percentile(boot_dds,5):6.2f}% or deeper")
    print(f"    Prob of losing money: {(boot_rets < 0).mean()*100:.1f}%")
    print("  Read: size for the worst-5% drawdown, not the median. And note")
    print("  how WIDE the bootstrap return range is -- that width is how")
    print("  little you actually know from a small sample of trades.")
    return {"reshuffle_dds": reshuffle_dds, "boot_returns": boot_rets, "boot_dds": boot_dds}


if __name__ == "__main__":
    raw = get_data()
    # forward-test on the last ~40% so it's genuinely out of sample
    cut = int(len(raw)*0.60)
    eq, tr = forward_simulate(raw.iloc[cut-200:])   # keep 200d warmup before cut
    if len(tr):
        monte_carlo_trades(tr["ret_pct"])
        print("\nFirst few paper trades:")
        print(tr.head(8).to_string(index=False))
