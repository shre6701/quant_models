# Trading Signals MCP Server

## Architecture

```
You (Claude Code) ←→ Kite MCP (market data) ←→ Zerodha
                  ←→ Trading-Signals MCP (compute) ←→ Telegram alerts
```

**Kite MCP** (official Zerodha): fetches live prices, historical data, holdings, positions
**Trading-Signals MCP** (this server): computes momentum/pairs signals, regime detection, position sizing, sends alerts

## First-Time Setup

1. Restart Claude Code in this directory (the `.claude/settings.json` registers both MCP servers)
2. On first Kite MCP call, you'll be prompted to log in via Zerodha's 2FA in your browser
3. After login, all Kite tools become available

## Daily Workflow (ask Claude)

### Morning scan:
"Fetch historical data for RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK from Kite and compute momentum signals for all of them"

### Check a specific pair:
"Get 90 days of TCS and INFY close prices from Kite, then compute the pair z-score"

### Regime check:
"Get Nifty 50 historical closes for the last 30 days and detect the market regime"

### Full signal fire:
"Scan all momentum tickers and pairs from my watchlist, alert me on Telegram for any actionable signals"

### Position sizing:
"I want to buy RELIANCE with 2L capital and 2% risk per trade. Get the current price from Kite and calculate position size."

## Tools Reference

### From Kite MCP (data):
- `get_historical_data` — OHLCV candles for any NSE ticker
- `get_ltp` — last traded price
- `get_quotes` — full quote with volume, bid/ask
- `search_instruments` — find ticker symbols
- `get_holdings` / `get_positions` — your portfolio
- `place_gtt_order` — place GTT (good-till-triggered) orders

### From Trading-Signals MCP (compute):
- `compute_momentum` — 50/200 SMA crossover signal
- `compute_pair` — pairs z-score signal
- `detect_regime` — market regime (trending/sideways/volatile)
- `batch_momentum` — scan multiple tickers at once
- `batch_pairs` — scan multiple pairs at once
- `position_size` — risk-based position sizing
- `send_alert` — send message to Telegram
- `alert_momentum` — format + send momentum alert
- `get_watchlist` — tracked tickers list

## Node Version

Both servers require Node 22+. The settings.json points directly to:
`C:\Users\shreyansh\.nvm\versions\node\v22.22.3\bin\node.exe`

If you update Node, update the path in `.claude/settings.json`.
