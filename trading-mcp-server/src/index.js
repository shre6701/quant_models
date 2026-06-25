import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import "dotenv/config";
import {
  TICKERS,
  computeMomentumSignal,
  computePairSignal,
  computeRegime,
} from "./market-data.js";
import {
  sendTelegramAlert,
  formatMomentumAlert,
  formatPairAlert,
} from "./alerts.js";
import { multiScan, scanStock } from "./strategies.js";

const server = new McpServer({
  name: "trading-signals",
  version: "2.0.0",
});

// --- Tool: compute momentum signal from Kite data ---
server.tool(
  "compute_momentum",
  `Compute 50/200 SMA crossover signal from historical close prices.
Feed this tool with data from Kite MCP's get_historical_data tool.
Input: ticker name + array of daily close prices (oldest first, need 201+ days).`,
  {
    ticker: z.string().describe("Ticker symbol, e.g. RELIANCE"),
    closes: z.array(z.number()).describe("Array of daily close prices, oldest first (need 201+ days)"),
    dates: z.array(z.string()).optional().describe("Optional: array of date strings matching closes"),
  },
  async ({ ticker, closes, dates }) => {
    const signal = computeMomentumSignal(closes, dates);
    return {
      content: [{ type: "text", text: JSON.stringify({ ticker, ...signal }, null, 2) }],
    };
  }
);

// --- Tool: compute pair signal from Kite data ---
server.tool(
  "compute_pair",
  `Compute pairs trading z-score signal from two stocks' historical close prices.
Feed this tool with data from Kite MCP's get_historical_data for both tickers.
Input: two tickers + their close price arrays (oldest first, need 70+ days).`,
  {
    ticker1: z.string().describe("First ticker, e.g. TCS"),
    ticker2: z.string().describe("Second ticker, e.g. INFY"),
    closes1: z.array(z.number()).describe("Daily closes for ticker1, oldest first"),
    closes2: z.array(z.number()).describe("Daily closes for ticker2, oldest first"),
    dates: z.array(z.string()).optional().describe("Optional: date strings"),
    lookback: z.number().optional().default(60).describe("Z-score lookback period (default 60)"),
  },
  async ({ ticker1, ticker2, closes1, closes2, dates, lookback }) => {
    const signal = computePairSignal(closes1, closes2, dates, lookback);
    return {
      content: [
        { type: "text", text: JSON.stringify({ pair: `${ticker1}/${ticker2}`, ...signal }, null, 2) },
      ],
    };
  }
);

// --- Tool: detect market regime ---
server.tool(
  "detect_regime",
  `Detect current market regime (TRENDING_UP, TRENDING_DOWN, SIDEWAYS, HIGH_VOL) from close prices.
Recommends which strategy to use. Feed with Nifty 50 or any index/stock closes.`,
  {
    ticker: z.string().describe("Ticker or index name, e.g. NIFTY50"),
    closes: z.array(z.number()).describe("Recent daily closes (20+ days), oldest first"),
    lookback: z.number().optional().default(20).describe("Lookback window (default 20 days)"),
  },
  async ({ ticker, closes, lookback }) => {
    const regime = computeRegime(closes, lookback);
    return {
      content: [{ type: "text", text: JSON.stringify({ ticker, ...regime }, null, 2) }],
    };
  }
);

// --- Tool: batch momentum scan ---
server.tool(
  "batch_momentum",
  `Compute momentum signals for multiple tickers at once.
Input: array of {ticker, closes} objects. Returns all signals + highlights actionable ones.`,
  {
    stocks: z.array(z.object({
      ticker: z.string(),
      closes: z.array(z.number()),
    })).describe("Array of {ticker, closes} objects"),
  },
  async ({ stocks }) => {
    const results = stocks.map(({ ticker, closes }) => ({
      ticker,
      ...computeMomentumSignal(closes),
    }));
    const actionable = results.filter((r) => r.signal === "BUY" || r.signal === "SELL");
    return {
      content: [{
        type: "text",
        text: JSON.stringify({ total: results.length, actionable_count: actionable.length, actionable, all: results }, null, 2),
      }],
    };
  }
);

// --- Tool: batch pairs scan ---
server.tool(
  "batch_pairs",
  `Compute pair signals for multiple pairs at once.
Input: array of {ticker1, ticker2, closes1, closes2} objects.`,
  {
    pairs: z.array(z.object({
      ticker1: z.string(),
      ticker2: z.string(),
      closes1: z.array(z.number()),
      closes2: z.array(z.number()),
    })).describe("Array of pair objects"),
  },
  async ({ pairs: pairData }) => {
    const results = pairData.map(({ ticker1, ticker2, closes1, closes2 }) => ({
      pair: `${ticker1}/${ticker2}`,
      ...computePairSignal(closes1, closes2),
    }));
    const actionable = results.filter(
      (r) => r.signal === "SHORT_SPREAD" || r.signal === "LONG_SPREAD"
    );
    return {
      content: [{
        type: "text",
        text: JSON.stringify({ total: results.length, actionable_count: actionable.length, actionable, all: results }, null, 2),
      }],
    };
  }
);

// --- Tool: position sizing ---
server.tool(
  "position_size",
  "Calculate position size for a trade given capital, price, and risk parameters.",
  {
    capital: z.number().describe("Total capital in INR"),
    price: z.number().describe("Current stock price (get from Kite get_ltp)"),
    ticker: z.string().describe("Ticker name"),
    risk_pct: z.number().optional().default(2).describe("Max risk per trade as % of capital (default 2%)"),
    stop_loss_pct: z.number().optional().default(8).describe("Stop-loss distance in % (default 8% for momentum)"),
  },
  async ({ capital, price, ticker, risk_pct, stop_loss_pct }) => {
    const riskAmount = capital * (risk_pct / 100);
    const shares = Math.floor(riskAmount / (price * (stop_loss_pct / 100)));
    const positionValue = shares * price;
    const costRoundTrip = 0.0054;

    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          ticker,
          current_price: price,
          shares_to_buy: shares,
          position_value: Math.round(positionValue),
          risk_per_trade: Math.round(riskAmount),
          stop_loss_price: Math.round(price * (1 - stop_loss_pct / 100) * 100) / 100,
          estimated_cost: Math.round(positionValue * costRoundTrip),
          pct_of_capital: Math.round((positionValue / capital) * 10000) / 100,
        }, null, 2),
      }],
    };
  }
);

// --- Tool: send Telegram alert ---
server.tool(
  "send_alert",
  "Send a trading alert message via Telegram.",
  {
    message: z.string().describe("Alert message to send (supports Markdown)"),
  },
  async ({ message }) => {
    const result = await sendTelegramAlert(message);
    return {
      content: [{ type: "text", text: JSON.stringify(result) }],
    };
  }
);

// --- Tool: format and send momentum alert ---
server.tool(
  "alert_momentum",
  "Format and send a momentum signal alert to Telegram.",
  {
    ticker: z.string(),
    signal: z.string().describe("BUY or SELL"),
    price: z.number(),
    sma50: z.number(),
    sma200: z.number(),
  },
  async ({ ticker, signal, price, sma50, sma200 }) => {
    const msg = formatMomentumAlert(ticker, {
      signal, last_price: price, fast: sma50, slow: sma200,
      spread_pct: Math.round(((sma50 - sma200) / sma200) * 10000) / 100,
      date: new Date().toISOString().split("T")[0],
    });
    const result = await sendTelegramAlert(msg);
    return { content: [{ type: "text", text: JSON.stringify({ message: msg, ...result }) }] };
  }
);

// --- Tool: get tracked tickers list ---
server.tool(
  "get_watchlist",
  "Returns the list of tracked tickers for momentum and pairs strategies.",
  {},
  async () => {
    return {
      content: [{
        type: "text",
        text: JSON.stringify(TICKERS, null, 2),
      }],
    };
  }
);

// --- Tool: multi-strategy scan (single stock) ---
server.tool(
  "scan_stock",
  `Run all 6 strategies on a single stock: Momentum SMA, 18 EMA Breakout, Gold Impulse, 80/20 Okala, Volume, ADX.
Input: ticker + OHLCV arrays (oldest first, need 201+ days for full coverage).`,
  {
    ticker: z.string(),
    opens: z.array(z.number()).describe("Daily open prices, oldest first"),
    highs: z.array(z.number()).describe("Daily high prices"),
    lows: z.array(z.number()).describe("Daily low prices"),
    closes: z.array(z.number()).describe("Daily close prices"),
    volumes: z.array(z.number()).describe("Daily volumes"),
  },
  async ({ ticker, opens, highs, lows, closes, volumes }) => {
    const result = scanStock(ticker, opens, highs, lows, closes, volumes);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }
);

// --- Tool: multi-strategy batch scan (100+ stocks) ---
server.tool(
  "multi_scan",
  `Run all 6 strategies on multiple stocks at once. Strategies: Momentum (50/200 SMA), 18 EMA Breakout, Gold Impulse (Elder), 80/20 Okala, Volume Spike, ADX Trend.
Returns priority-ranked results with actionable signals highlighted.
Input: array of {ticker, opens, highs, lows, closes, volumes}. Need 201+ days for full coverage.`,
  {
    stocks: z.array(z.object({
      ticker: z.string(),
      opens: z.array(z.number()),
      highs: z.array(z.number()),
      lows: z.array(z.number()),
      closes: z.array(z.number()),
      volumes: z.array(z.number()),
    })).describe("Array of stock OHLCV objects"),
  },
  async ({ stocks }) => {
    const result = multiScan(stocks);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }
);

// --- Start server ---
const transport = new StdioServerTransport();
await server.connect(transport);
