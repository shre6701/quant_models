# Multi-Strategy Scanner — Usage Guide

## Architecture

One OHLCV fetch per stock → all 6 strategies computed in a single pass → results ranked by priority.

## Strategies

| # | Strategy | Min Data | Signal Types |
|---|----------|----------|--------------|
| 1 | **Momentum SMA** (50/200) | 201 days | BUY, SELL, BULLISH, BEARISH |
| 2 | **18 EMA Breakout** | 25 days | BUY, SELL, ABOVE_EMA, BELOW_EMA |
| 3 | **Gold Impulse** (Elder) | 40 days | BUY (green), SELL (red), NEUTRAL (blue) |
| 4 | **80/20 Okala** | 3 days | BUY, SELL, BULLISH_SETUP, BEARISH_SETUP |
| 5 | **Volume Spike** | 21 days | BREAKOUT_VOLUME, SELLOFF_VOLUME, HIGH_BULLISH |
| 6 | **ADX Trend** (14) | 29 days | TREND_BUY, TREND_SELL, NO_TREND |

## Priority Scoring

- Each actionable signal (BUY/SELL/BREAKOUT) = +10 points
- ADX > 25 confirmation with any actionable signal = +5
- Volume ratio > 2x with actionable = +3
- Results sorted descending by score

## Optimal Scan Workflow (100 stocks)

### Step 1: Fetch OHLCV (batch via Kite)
```
For each stock: get_historical_data(ticker, "day", from=1yr_ago, to=today)
→ Extract: opens[], highs[], lows[], closes[], volumes[]
```

### Step 2: Call multi_scan
```
multi_scan({ stocks: [ {ticker, opens, highs, lows, closes, volumes}, ... ] })
```

### Step 3: Act on results
- Priority score > 0 → review signals
- Multiple strategies aligning (e.g., EMA18 BUY + Gold Impulse GREEN + Volume spike) = high conviction
- ADX < 20 → ignore momentum/breakout signals (ranging market)

## Batching for 100 Stocks

Kite rate limits: ~3 req/sec for historical data.
Recommended: fetch in batches of 10, 100ms delay between batches.
Total time: ~35-40 seconds for 100 stocks.

Then pass ALL to multi_scan in one call (server-side compute is instant).

## Signal Confluence Rules

| Confluence | Confidence | Action |
|-----------|-----------|--------|
| ADX trending + Momentum BUY + Volume spike | HIGH | Enter immediately |
| EMA18 BUY + Gold Impulse GREEN | MEDIUM-HIGH | Enter on pullback |
| 80/20 setup + Volume dry-up | MEDIUM | Wait for trigger |
| Single strategy only | LOW | Watch, don't trade |
