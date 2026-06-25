# Quant Trading Workstation — Guide

## What This Is

A systematic daily stock analysis system for Indian equities (NSE). You add tickers to a spreadsheet, run one command, and get back a decision matrix telling you exactly what to trade, in which direction, for how long, and with what position size.

---

## Folder Map

```
quant_models/
│
├── daily_analysis.py        ← MAIN ENTRY POINT. Run this every day.
├── watchlist.xlsx           ← YOUR INPUT. Add tickers here.
├── analysis_output.xlsx     ← YOUR OUTPUT. Decisions land here.
│
├── engine/                  ← Core library (don't edit unless extending)
│   ├── indicators.py        Technical indicators (SMA, EMA, RSI, ADX, ATR)
│   ├── strategies.py        6-strategy signal scanner
│   ├── backtest.py          Walk-forward backtest + Monte Carlo
│   ├── recommendation.py    Decision engine + position sizing
│   └── data.py              Data fetching (Yahoo Finance)
│
├── trading-mcp-server/      ← MCP server for Claude Code integration
│   └── src/
│       ├── index.js          MCP tool registration
│       ├── strategies.js     Same 6 strategies (JS version for real-time)
│       ├── market-data.js    Momentum/pairs/regime signals
│       └── alerts.js         Telegram notifications
│
├── batch_test.py            ← Run RSI-2 backtest across many tickers at once
├── forward_and_montecarlo.py← Standalone forward sim + Monte Carlo
│
└── Notebooks (research/exploration, not needed for daily workflow):
    ├── mean_reversion_backtest.ipynb
    ├── momentum_and_pairs.ipynb
    ├── regime_filter_v3.ipynb
    ├── filtered_strategy_v2.ipynb
    └── fundamental_filter_exploration.ipynb
```

---

## Setup (One-Time)

### 1. Install Python dependencies

```bash
pip install yfinance pandas numpy openpyxl
```

### 2. First run (creates template watchlist)

```bash
cd quant_models
python daily_analysis.py
```

This creates `watchlist.xlsx` with 10 sample tickers. Edit it with your own.

---

## Daily Workflow

### Step 1: Update your watchlist

Open `watchlist.xlsx` in Excel/LibreOffice. The sheet has three columns:

| ticker | date_added | notes |
|--------|-----------|-------|
| RELIANCE | 2026-06-25 | Watching for breakout |
| ZOMATO | 2026-06-25 | Post-earnings |

- **ticker** — NSE symbol (no `.NS` suffix needed, it's added automatically)
- **date_added** — when you added it (for your reference)
- **notes** — optional, for your own context

Add or remove rows as needed. Save and close.

### Step 2: Run the analysis

```bash
python daily_analysis.py
```

Options:
```bash
python daily_analysis.py --capital 200000    # position size for 2L capital
python daily_analysis.py --date 2026-06-25   # tag output with specific date
```

Takes ~10-15 seconds per ticker (fetching 3 years of data + backtest).

### Step 3: Read the output

The console prints a quick summary:

```
  Ticker     Action               Conf   Qty     Stop Reason
  ---------- -------------------- ---- ----- -------- --------
  WIPRO      SWING SHORT           56%   103   164.78 Trending ADX=25.58, 2 signals
  HDFCBANK   SWING LONG            10%    31   761.06 Single signal, reduce size
```

For the full picture, open `analysis_output.xlsx`. It has three sheets:

| Sheet | What's in it |
|-------|-------------|
| **Summary** | One row per ticker: recommendation, confidence, qty, stop, reason |
| **Analysis** | Full detail: all 6 signals, backtest stats, Monte Carlo, risk notes |
| **History** | Accumulates across runs — see how signals evolve day-over-day |

---

## Understanding the Output

### Recommendations

| Type | Meaning | Hold Period | When it triggers |
|------|---------|-------------|------------------|
| POSITIONAL LONG | Strong buy, hold for weeks | 1-4 weeks | ADX>30 + 3+ signals aligned |
| POSITIONAL SHORT | Strong sell, hold for weeks | 1-4 weeks | ADX>30 + 3+ sell signals |
| SWING LONG | Buy, hold for days | 2-7 days | Trending + 2+ buy signals |
| SWING SHORT | Sell, hold for days | 2-7 days | Trending + 2+ sell signals |
| SCALPING LONG | Intraday buy | Hours | Volume spike + tight ATR |
| SCALPING SHORT | Intraday sell | Hours | Volume spike + tight ATR |
| NO TRADE | Stay out | — | No confluence or no backtest edge |

### Confidence Score (0-100%)

- **60-100%** — High conviction. Multiple signals confirm, backtest validates edge.
- **30-60%** — Moderate. Direction is clear but fewer confirmations.
- **10-30%** — Low. Single signal, use reduced size.
- **0%** — No trade. Either conflicting signals or backtest shows no edge.

### Position Sizing

- **qty** — How many shares to buy, based on 1% capital risk per trade
- **stop_loss** — Where to place your stop (2x ATR below entry for longs)
- **risk_amt** — Maximum rupees you'll lose if stopped out

### Key Columns in the Analysis Sheet

| Column | What it tells you |
|--------|------------------|
| momentum | 50/200 SMA crossover (BUY/SELL/BULLISH/BEARISH) |
| ema18 | 18 EMA breakout (BUY/SELL/ABOVE/BELOW) |
| impulse | Elder's Gold Impulse — EMA13 + MACD (BUY/SELL/NEUTRAL) |
| 8020 | 80/20 candle body strategy (BUY/SELL/SETUP/NO_SETUP) |
| volume | Volume spike detection (BREAKOUT/SELLOFF/NORMAL) |
| adx | ADX trend + DI crossover (TREND_BUY/TREND_SELL/NO_TREND) |
| regime | Market regime (TRENDING/RANGING/WEAK_TREND) |
| bt_ret_% | Backtest return (out-of-sample, last 40% of data) |
| bt_wr_% | Win rate from backtest |
| mc_loss_prob_% | Monte Carlo probability of losing money |

---

## How the Decision Engine Works

```
         Yahoo Finance (3 years OHLCV)
                    |
    ┌───────────────┼───────────────┐
    |               |               |
 6 Strategies   Backtest (OOS)   Monte Carlo
    |               |               |
    └───────────────┼───────────────┘
                    |
           Recommendation Engine
                    |
    ┌───────────────┼───────────────┐
    |               |               |
Direction       Timeframe        Gating
(BUY vs SELL    (ADX + vol       (must have
 signal count)   ratio)          backtest edge)
```

**Gating rules (why you get NO TRADE):**
1. No actionable signals from any of the 6 strategies
2. Buy/sell signals cancel each other out (conflicting)
3. Backtest return is negative (strategy doesn't work on this stock)
4. Monte Carlo shows >45% probability of losing money

---

## Tips

- **Don't chase high confidence alone.** A 70% confidence on a stock with -15% backtest drawdown is still risky. Check `mc_worst_dd_%`.
- **History sheet is your journal.** After a week, compare what you actually traded vs what the system recommended. Track your hit rate.
- **NO TRADE is the most common output.** That's by design. The system is conservative — it'd rather miss a trade than put you in a bad one.
- **Add tickers before market open.** Run the script at 9:00 AM, review the output, and place orders by 9:15.
- **Reduce size on low confidence.** If confidence is <30%, the system prints "reduce size" — take half the suggested qty.

---

## Extending the System

### Add a new strategy

1. Add a function in `engine/strategies.py` following the same pattern (returns dict with `signal`, `actionable`, `strength`)
2. Add it to `run_all_strategies()`
3. Add its signal names to `BULLISH_SIGNALS` or `BEARISH_SIGNALS` in `engine/recommendation.py`

### Use Kite for live data

The `engine/data.py` `fetch_ohlcv()` function accepts a `source` parameter. To add Kite:
- Use the `mcp__kite__get_historical_data` tool via Claude Code for real-time data
- Or extend `data.py` with a `_fetch_kite()` function using the Kite Connect API

### Run batch backtest on a new strategy

```bash
python batch_test.py
```

Edit `TICKERS` list in that file to test across different stocks.

---

## Notebooks (for research only)

These are exploration notebooks, not part of the daily workflow:

| Notebook | Purpose |
|----------|---------|
| `mean_reversion_backtest.ipynb` | Learn honest backtesting (costs, OOS split, overfitting traps) |
| `momentum_and_pairs.ipynb` | Explore momentum and pairs trading strategies |
| `regime_filter_v3.ipynb` | Regime detection experiments |
| `filtered_strategy_v2.ipynb` | RSI-2 with fundamental filters (Screener.in + quarterly rebalance) |
| `fundamental_filter_exploration.ipynb` | Piotroski/Z-Score fundamental screening |

Use these to develop new strategies, then port the logic into `engine/strategies.py` for daily use.
