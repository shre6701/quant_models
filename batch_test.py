"""
batch_test.py
=============
Run the RSI-2 mean-reversion strategy across MANY tickers at once and
produce a single comparison table. The point is NOT to find the best
stock to trade -- that's the overfitting trap. The point is to see how
the strategy behaves ACROSS stocks. If results scatter wildly, there's
no stable edge; you're looking at noise.

Each ticker gets:
  - forward-sim return + max drawdown (one realized path)
  - bootstrap 5th-95th percentile return range (the uncertainty)
  - probability of losing money

USAGE (on your machine, in your venv, after `pip install yfinance`):
    python batch_test.py

Edit the TICKERS list and the USE_REAL_DATA flag below.
"""

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
USE_REAL_DATA = True   # set True on your machine (Yahoo reachable there)
TICKERS = [
    "RELIANCE.NS", "HDFCBANK.NS", "BBOX.NS", "WIPRO.NS", "RPTECH.NS",
    "ITC.NS", "IDEAFORGE.NS", "ZAGGLE.NS", "CGPOWER.NS", "BLS.NS",
]
START, END = "2021-01-01", "2026-05-31"
CAPITAL = 50000


# ----------------------------------------------------------------------
# DATA
# ----------------------------------------------------------------------
def make_synthetic(seed, n_days=1500):
    """Different seed per ticker so synthetic stocks aren't identical."""
    rng = np.random.default_rng(seed)
    trend = np.cumsum(np.full(n_days, rng.uniform(0.0001, 0.0005)))
    mr = np.zeros(n_days)
    theta = rng.uniform(0.08, 0.20)
    sigma = rng.uniform(0.008, 0.016)
    for t in range(1, n_days):
        mr[t] = mr[t-1]*(1-theta) + rng.normal(0, sigma)
    price = np.exp(4.6 + trend + mr)
    return pd.DataFrame({"Close": price},
                        index=pd.bdate_range("2018-01-01", periods=n_days))

def load_ticker(ticker, idx):
    if USE_REAL_DATA:
        import yfinance as yf
        df = yf.download(ticker, start=START, end=END, progress=False)
        if df.empty:
            return None
        df = df[["Close"]].dropna()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel("Ticker")
        return df
    else:
        return make_synthetic(seed=idx + 1)


# ----------------------------------------------------------------------
# STRATEGY PIECES
# ----------------------------------------------------------------------
def rsi(s, p=2):
    d = s.diff(); g = d.clip(lower=0); l = -d.clip(upper=0)
    ag = g.ewm(alpha=1/p, adjust=False).mean()
    al = l.ewm(alpha=1/p, adjust=False).mean()
    return 100 - (100/(1 + ag/al.replace(0, np.nan)))

def cost():
    return 0.001 + 0.0000345 + 0.18*0.0000345 + 0.00015 + 0.000001 + 0.0015

def forward_sim(raw, warmup=200, rsi_entry=10, capital=CAPITAL):
    c = cost(); closes = raw["Close"]; dates = raw.index
    cash, sh, inpos, ep = capital, 0, False, 0.0
    rets, eqs = [], []
    for i in range(warmup, len(raw)):
        w = closes.iloc[:i+1]; pt = w.iloc[-1]
        sl = w.tail(200).mean(); se = w.tail(5).mean(); rt = rsi(w).iloc[-1]
        if not inpos:
            if rt < rsi_entry and pt > sl:
                sh = int(cash // (pt*(1+c)))
                if sh > 0: cash -= sh*pt*(1+c); inpos, ep = True, pt
        else:
            if pt > se:
                cash += sh*pt*(1-c); rets.append((pt/ep-1)*100); sh, inpos = 0, False
        eqs.append(cash + sh*pt)
    eq = pd.Series(eqs, index=dates[warmup:])
    return eq, rets

def bootstrap(rets, n=3000, capital=CAPITAL, seed=1):
    if len(rets) < 2:
        return None
    rng = np.random.default_rng(seed)
    r = np.array(rets)/100; k = len(r)
    finals = []
    for _ in range(n):
        s = r[rng.integers(0, k, k)]
        finals.append((np.prod(1+s) - 1)*100)
    finals = np.array(finals)
    return {
        "p5": np.percentile(finals, 5),
        "p50": np.median(finals),
        "p95": np.percentile(finals, 95),
        "p_loss": (finals < 0).mean()*100,
    }


# ----------------------------------------------------------------------
# RUN ALL
# ----------------------------------------------------------------------
def main():
    rows = []
    print(f"Testing {len(TICKERS)} tickers "
          f"({'REAL data' if USE_REAL_DATA else 'SYNTHETIC data'})...\n")
    for idx, t in enumerate(TICKERS):
        raw = load_ticker(t, idx)
        if raw is None or len(raw) < 300:
            print(f"  {t}: no/insufficient data, skipped")
            continue
        cut = max(200, int(len(raw)*0.6) - 200)
        eq, rets = forward_sim(raw.iloc[cut:])
        realized = (eq.iloc[-1]/CAPITAL - 1)*100
        dd = ((eq - eq.cummax())/eq.cummax()).min()*100
        bs = bootstrap(rets)
        traded = raw.iloc[cut:]
        window = traded.iloc[200:]
        buyhold = (window["Close"].iloc[-1]/window["Close"].iloc[0] - 1)*100
        rows.append({
            "ticker": t,
            "trades": len(rets),
            "realized_%": round(realized, 1),
            "max_dd_%": round(dd, 1),
            "boot_5th_%": round(bs["p5"], 1) if bs else None,
            "boot_median_%": round(bs["p50"], 1) if bs else None,
            "boot_95th_%": round(bs["p95"], 1) if bs else None,
            "p_loss_%": round(bs["p_loss"], 0) if bs else None,
            "buyhold_%": round(buyhold, 1),
            "beat_hold": "YES" if realized > buyhold else "no",
        })

    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print("\n" + "="*70)
    print("HOW TO READ THIS TABLE:")
    print(" - Look at realized_% across all 10. Wildly different = no stable edge.")
    print(" - boot_5th to boot_95th is the UNCERTAINTY per stock. If that range")
    print("   straddles zero, you can't claim the strategy 'works' on it.")
    print(" - DO NOT pick the best realized_% stock and trade it. That's")
    print("   selecting noise. Judge the strategy as a whole, across all 10.")
    print(" - Median of realized_% vs a buy-and-hold of the same names is the")
    print("   real question. If the strategy can't beat holding, it's not worth it.")
    print("="*70)

if __name__ == "__main__":
    main()
