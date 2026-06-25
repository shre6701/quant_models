const TICKERS = {
  momentum: [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "ITC", "WIPRO",
    "SBIN", "INFY", "TCS", "LT", "BHARTIARTL",
    "TATAMOTORS", "MARUTI", "AXISBANK", "KOTAKBANK", "HINDUNILVR",
  ],
  pairs: [
    ["TCS", "INFY"],
    ["HDFCBANK", "ICICIBANK"],
    ["SBIN", "AXISBANK"],
    ["WIPRO", "INFY"],
    ["RELIANCE", "BHARTIARTL"],
  ],
};

function sma(closes, period) {
  if (closes.length < period) return null;
  const slice = closes.slice(-period);
  return slice.reduce((a, b) => a + b, 0) / period;
}

function computeMomentumSignal(closes, dates) {
  if (!closes || closes.length < 201) {
    return { signal: "INSUFFICIENT_DATA", detail: `Need 201 days, got ${closes?.length || 0}` };
  }

  const fast = sma(closes, 50);
  const slow = sma(closes, 200);

  const prevCloses = closes.slice(0, -1);
  const fastPrev = sma(prevCloses, 50);
  const slowPrev = sma(prevCloses, 200);

  let signal = "HOLD";
  if (fast > slow && fastPrev <= slowPrev) signal = "BUY";
  else if (fast < slow && fastPrev >= slowPrev) signal = "SELL";
  else if (fast > slow) signal = "BULLISH";
  else signal = "BEARISH";

  return {
    signal,
    sma50: Math.round(fast * 100) / 100,
    sma200: Math.round(slow * 100) / 100,
    spread_pct: Math.round(((fast - slow) / slow) * 10000) / 100,
    last_price: closes[closes.length - 1],
    date: dates?.[dates.length - 1] || null,
  };
}

function computePairSignal(closes1, closes2, dates, lookback = 60) {
  const len = Math.min(closes1.length, closes2.length);
  const c1 = closes1.slice(-len);
  const c2 = closes2.slice(-len);

  if (len < lookback + 10) {
    return { signal: "INSUFFICIENT_DATA", detail: `Need ${lookback + 10} days, got ${len}` };
  }

  const spread = c1.map((p, i) => Math.log(p / c2[i]));
  const recent = spread.slice(-lookback);
  const mean = recent.reduce((a, b) => a + b, 0) / recent.length;
  const std = Math.sqrt(
    recent.reduce((a, b) => a + (b - mean) ** 2, 0) / recent.length
  );

  const currentSpread = spread[spread.length - 1];
  const zScore = std > 0 ? (currentSpread - mean) / std : 0;

  let signal = "NO_SIGNAL";
  let action = null;
  if (zScore > 2.0) {
    signal = "SHORT_SPREAD";
    action = `Buy Stock B (laggard), spread is +${zScore.toFixed(2)} sigma`;
  } else if (zScore < -2.0) {
    signal = "LONG_SPREAD";
    action = `Buy Stock A (laggard), spread is ${zScore.toFixed(2)} sigma`;
  } else if (Math.abs(zScore) < 0.5) {
    signal = "AT_MEAN";
    action = "Spread at mean — close position if open";
  }

  return {
    signal,
    z_score: Math.round(zScore * 100) / 100,
    spread_mean: Math.round(mean * 10000) / 10000,
    spread_std: Math.round(std * 10000) / 10000,
    current_spread: Math.round(currentSpread * 10000) / 10000,
    action,
    date: dates?.[dates.length - 1] || null,
  };
}

function computeRegime(closes, lookback = 20) {
  if (closes.length < lookback + 1) return { regime: "UNKNOWN" };

  const returns = [];
  for (let i = closes.length - lookback; i < closes.length; i++) {
    returns.push(closes[i] / closes[i - 1] - 1);
  }

  const vol = Math.sqrt(returns.reduce((a, r) => a + r * r, 0) / returns.length) * Math.sqrt(252);
  const drift = (closes[closes.length - 1] / closes[closes.length - lookback] - 1) * (252 / lookback);

  let regime;
  if (vol > 0.25) regime = "HIGH_VOL";
  else if (drift > 0.15 && vol < 0.20) regime = "TRENDING_UP";
  else if (drift < -0.15 && vol < 0.20) regime = "TRENDING_DOWN";
  else regime = "SIDEWAYS";

  const recommended = {
    "HIGH_VOL": "CASH — sit out, both strategies whipsaw",
    "TRENDING_UP": "MOMENTUM — ride the trend with 50/200 SMA",
    "TRENDING_DOWN": "CASH or PAIRS — avoid momentum long-only",
    "SIDEWAYS": "PAIRS — spread mean-reversion works in ranges",
  };

  return {
    regime,
    annualized_vol: Math.round(vol * 10000) / 100,
    annualized_drift: Math.round(drift * 10000) / 100,
    strategy_recommendation: recommended[regime],
  };
}

export { TICKERS, computeMomentumSignal, computePairSignal, computeRegime, sma };
