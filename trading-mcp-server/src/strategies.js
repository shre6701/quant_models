// --- Indicator primitives ---

function sma(data, period) {
  if (data.length < period) return null;
  const slice = data.slice(-period);
  return slice.reduce((a, b) => a + b, 0) / period;
}

function ema(data, period) {
  if (data.length < period) return null;
  const k = 2 / (period + 1);
  let val = data.slice(0, period).reduce((a, b) => a + b, 0) / period;
  for (let i = period; i < data.length; i++) {
    val = data[i] * k + val * (1 - k);
  }
  return val;
}

function emaArray(data, period) {
  if (data.length < period) return [];
  const k = 2 / (period + 1);
  const result = [];
  let val = data.slice(0, period).reduce((a, b) => a + b, 0) / period;
  result.push(val);
  for (let i = period; i < data.length; i++) {
    val = data[i] * k + val * (1 - k);
    result.push(val);
  }
  return result;
}

function trueRange(high, low, close, i) {
  if (i === 0) return high[0] - low[0];
  return Math.max(
    high[i] - low[i],
    Math.abs(high[i] - close[i - 1]),
    Math.abs(low[i] - close[i - 1])
  );
}

function computeADX(highs, lows, closes, period = 14) {
  const len = highs.length;
  if (len < period * 2 + 1) return { adx: null, plusDI: null, minusDI: null };

  const tr = [];
  const plusDM = [];
  const minusDM = [];

  for (let i = 0; i < len; i++) {
    tr.push(trueRange(highs, lows, closes, i));
    if (i === 0) {
      plusDM.push(0);
      minusDM.push(0);
    } else {
      const upMove = highs[i] - highs[i - 1];
      const downMove = lows[i - 1] - lows[i];
      plusDM.push(upMove > downMove && upMove > 0 ? upMove : 0);
      minusDM.push(downMove > upMove && downMove > 0 ? downMove : 0);
    }
  }

  const smoothedTR = wilderSmooth(tr, period);
  const smoothedPlusDM = wilderSmooth(plusDM, period);
  const smoothedMinusDM = wilderSmooth(minusDM, period);

  const dx = [];
  let plusDI, minusDI;
  for (let i = 0; i < smoothedTR.length; i++) {
    plusDI = smoothedTR[i] > 0 ? (smoothedPlusDM[i] / smoothedTR[i]) * 100 : 0;
    minusDI = smoothedTR[i] > 0 ? (smoothedMinusDM[i] / smoothedTR[i]) * 100 : 0;
    const sum = plusDI + minusDI;
    dx.push(sum > 0 ? (Math.abs(plusDI - minusDI) / sum) * 100 : 0);
  }

  const adxArr = wilderSmooth(dx, period);
  const adx = adxArr[adxArr.length - 1];
  return { adx: r2(adx), plusDI: r2(plusDI), minusDI: r2(minusDI) };
}

function wilderSmooth(data, period) {
  if (data.length < period) return [];
  let val = data.slice(0, period).reduce((a, b) => a + b, 0);
  const result = [val];
  for (let i = period; i < data.length; i++) {
    val = val - val / period + data[i];
    result.push(val);
  }
  return result;
}

function r2(v) {
  return v == null ? null : Math.round(v * 100) / 100;
}

// --- Strategy 1: 50/200 SMA Momentum Crossover ---

function momentumSignal(closes) {
  if (closes.length < 201) return null;
  const fast = sma(closes, 50);
  const slow = sma(closes, 200);
  const prev = closes.slice(0, -1);
  const fastPrev = sma(prev, 50);
  const slowPrev = sma(prev, 200);

  let signal = "HOLD";
  if (fast > slow && fastPrev <= slowPrev) signal = "BUY";
  else if (fast < slow && fastPrev >= slowPrev) signal = "SELL";
  else if (fast > slow) signal = "BULLISH";
  else signal = "BEARISH";

  return {
    strategy: "MOMENTUM_SMA",
    signal,
    sma50: r2(fast),
    sma200: r2(slow),
    spread_pct: r2(((fast - slow) / slow) * 100),
  };
}

// --- Strategy 2: 18 EMA Breakout ---

function ema18Breakout(closes) {
  if (closes.length < 25) return null;
  const ema18 = emaArray(closes, 18);
  const offset = closes.length - ema18.length;

  const curr = closes[closes.length - 1];
  const prev = closes[closes.length - 2];
  const emaToday = ema18[ema18.length - 1];
  const emaYesterday = ema18[ema18.length - 2];

  let signal = "HOLD";
  if (prev < emaYesterday && curr > emaToday) signal = "BUY";
  else if (prev > emaYesterday && curr < emaToday) signal = "SELL";
  else if (curr > emaToday) signal = "ABOVE_EMA";
  else signal = "BELOW_EMA";

  return {
    strategy: "EMA18_BREAKOUT",
    signal,
    price: curr,
    ema18: r2(emaToday),
    distance_pct: r2(((curr - emaToday) / emaToday) * 100),
  };
}

// --- Strategy 3: Elder's Gold Impulse (EMA13 + MACD Histogram) ---

function goldImpulse(closes) {
  if (closes.length < 40) return null;
  const ema13 = emaArray(closes, 13);
  const ema12 = emaArray(closes, 12);
  const ema26 = emaArray(closes, 26);

  const macdLine = [];
  const minLen = Math.min(ema12.length, ema26.length);
  const e12 = ema12.slice(-minLen);
  const e26 = ema26.slice(-minLen);
  for (let i = 0; i < minLen; i++) {
    macdLine.push(e12[i] - e26[i]);
  }
  const signalLine = emaArray(macdLine, 9);
  const histLen = Math.min(macdLine.length, signalLine.length);
  const macdHist = [];
  for (let i = 0; i < histLen; i++) {
    macdHist.push(macdLine[macdLine.length - histLen + i] - signalLine[signalLine.length - histLen + i]);
  }

  if (macdHist.length < 2 || ema13.length < 2) return null;

  const emaRising = ema13[ema13.length - 1] > ema13[ema13.length - 2];
  const emaFalling = ema13[ema13.length - 1] < ema13[ema13.length - 2];
  const histRising = macdHist[macdHist.length - 1] > macdHist[macdHist.length - 2];
  const histFalling = macdHist[macdHist.length - 1] < macdHist[macdHist.length - 2];

  let color, signal;
  if (emaRising && histRising) {
    color = "GREEN";
    signal = "BUY";
  } else if (emaFalling && histFalling) {
    color = "RED";
    signal = "SELL";
  } else {
    color = "BLUE";
    signal = "NEUTRAL";
  }

  return {
    strategy: "GOLD_IMPULSE",
    signal,
    color,
    ema13: r2(ema13[ema13.length - 1]),
    macd_hist: r2(macdHist[macdHist.length - 1]),
  };
}

// --- Strategy 4: 80/20 Strategy (Okala) ---

function strategy8020(opens, highs, lows, closes) {
  if (closes.length < 3) return null;
  const n = closes.length;

  const bodyPrev = Math.abs(closes[n - 2] - opens[n - 2]);
  const rangePrev = highs[n - 2] - lows[n - 2];
  if (rangePrev === 0) return null;
  const bodyRatio = bodyPrev / rangePrev;

  const isBullishCandle = closes[n - 2] > opens[n - 2];
  const isBearishCandle = closes[n - 2] < opens[n - 2];
  const is8020 = bodyRatio >= 0.80;

  if (!is8020) {
    return { strategy: "STRATEGY_8020", signal: "NO_SETUP", body_ratio: r2(bodyRatio * 100) };
  }

  const todayClose = closes[n - 1];
  let signal = "SETUP_PENDING";

  if (isBullishCandle && todayClose < lows[n - 2]) {
    signal = "SELL";
  } else if (isBearishCandle && todayClose > highs[n - 2]) {
    signal = "BUY";
  } else if (isBullishCandle) {
    signal = "BEARISH_SETUP";
  } else if (isBearishCandle) {
    signal = "BULLISH_SETUP";
  }

  return {
    strategy: "STRATEGY_8020",
    signal,
    body_ratio: r2(bodyRatio * 100),
    trigger_candle: isBullishCandle ? "BULLISH" : "BEARISH",
    prev_high: highs[n - 2],
    prev_low: lows[n - 2],
  };
}

// --- Strategy 5: Volume Spike Detection ---

function volumeAnalysis(volumes, closes) {
  if (volumes.length < 21) return null;
  const avgVol = sma(volumes.slice(0, -1), 20);
  const todayVol = volumes[volumes.length - 1];
  const ratio = todayVol / avgVol;

  const priceChange = closes.length >= 2
    ? ((closes[closes.length - 1] - closes[closes.length - 2]) / closes[closes.length - 2]) * 100
    : 0;

  let signal = "NORMAL";
  if (ratio > 2.5 && priceChange > 1) signal = "BREAKOUT_VOLUME";
  else if (ratio > 2.5 && priceChange < -1) signal = "SELLOFF_VOLUME";
  else if (ratio > 1.5 && priceChange > 0.5) signal = "HIGH_BULLISH";
  else if (ratio > 1.5 && priceChange < -0.5) signal = "HIGH_BEARISH";
  else if (ratio < 0.5) signal = "DRY_UP";

  return {
    strategy: "VOLUME",
    signal,
    vol_ratio: r2(ratio),
    avg_volume: Math.round(avgVol),
    today_volume: todayVol,
    price_change_pct: r2(priceChange),
  };
}

// --- Strategy 6: ADX Regime + DI Crossover ---

function adxStrategy(highs, lows, closes) {
  const { adx, plusDI, minusDI } = computeADX(highs, lows, closes, 14);
  if (adx == null) return null;

  let regime, signal;
  if (adx > 25) {
    regime = "TRENDING";
    signal = plusDI > minusDI ? "TREND_BUY" : "TREND_SELL";
  } else if (adx < 20) {
    regime = "RANGING";
    signal = "NO_TREND";
  } else {
    regime = "WEAK_TREND";
    signal = plusDI > minusDI ? "LEAN_BULLISH" : "LEAN_BEARISH";
  }

  return {
    strategy: "ADX",
    signal,
    adx,
    plusDI,
    minusDI,
    regime,
  };
}

// --- Master Scanner ---

function scanStock(ticker, opens, highs, lows, closes, volumes) {
  const results = {
    ticker,
    last_price: closes[closes.length - 1],
    signals: {},
    actionable: [],
  };

  const adx = adxStrategy(highs, lows, closes);
  if (adx) results.signals.adx = adx;

  const mom = momentumSignal(closes);
  if (mom) results.signals.momentum = mom;

  const ema18 = ema18Breakout(closes);
  if (ema18) results.signals.ema18_breakout = ema18;

  const impulse = goldImpulse(closes);
  if (impulse) results.signals.gold_impulse = impulse;

  const eighty = strategy8020(opens, highs, lows, closes);
  if (eighty) results.signals.strategy_8020 = eighty;

  const vol = volumeAnalysis(volumes, closes);
  if (vol) results.signals.volume = vol;

  const actionableSignals = ["BUY", "SELL", "BREAKOUT_VOLUME", "SELLOFF_VOLUME"];
  for (const [key, val] of Object.entries(results.signals)) {
    if (actionableSignals.includes(val.signal)) {
      results.actionable.push({ strategy: key, signal: val.signal });
    }
  }

  // Priority score: more actionable signals + ADX confirmation = higher priority
  let score = results.actionable.length * 10;
  if (adx && adx.adx > 25 && results.actionable.length > 0) score += 5;
  if (vol && vol.vol_ratio > 2) score += 3;
  results.priority_score = score;

  return results;
}

function multiScan(stocks) {
  const results = stocks.map(({ ticker, opens, highs, lows, closes, volumes }) =>
    scanStock(ticker, opens, highs, lows, closes, volumes)
  );

  results.sort((a, b) => b.priority_score - a.priority_score);

  const actionable = results.filter((r) => r.actionable.length > 0);
  const summary = {
    total_scanned: results.length,
    actionable_count: actionable.length,
    regime_breakdown: {
      trending: results.filter((r) => r.signals.adx?.regime === "TRENDING").length,
      ranging: results.filter((r) => r.signals.adx?.regime === "RANGING").length,
      weak: results.filter((r) => r.signals.adx?.regime === "WEAK_TREND").length,
    },
  };

  return { summary, actionable, all: results };
}

export {
  multiScan,
  scanStock,
  momentumSignal,
  ema18Breakout,
  goldImpulse,
  strategy8020,
  volumeAnalysis,
  adxStrategy,
  computeADX,
  sma,
  ema,
  emaArray,
};
