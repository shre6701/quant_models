"""
Six-strategy signal scanner. Each strategy returns a standardized dict:
  {signal, actionable, strength, ...strategy-specific fields}

Strength is a float 0-1 indicating how extreme the signal is.
"""

import numpy as np
from .indicators import sma, ema_array, compute_adx, compute_atr


def strategy_momentum_sma(closes):
    if len(closes) < 201:
        return {"strategy": "MOMENTUM_SMA", "signal": "INSUFFICIENT_DATA", "actionable": False, "strength": 0}
    fast = sma(closes, 50)
    slow = sma(closes, 200)
    fast_prev = sma(closes[:-1], 50)
    slow_prev = sma(closes[:-1], 200)

    spread = (fast - slow) / slow * 100

    if fast > slow and fast_prev <= slow_prev:
        sig, strength = "BUY", 0.9
    elif fast < slow and fast_prev >= slow_prev:
        sig, strength = "SELL", 0.9
    elif fast > slow:
        sig, strength = "BULLISH", min(spread / 10, 0.7)
    else:
        sig, strength = "BEARISH", min(abs(spread) / 10, 0.7)

    return {
        "strategy": "MOMENTUM_SMA", "signal": sig, "actionable": sig in ("BUY", "SELL"),
        "strength": round(strength, 2), "sma50": round(fast, 2),
        "sma200": round(slow, 2), "spread_pct": round(spread, 2),
    }


def strategy_ema18(closes):
    if len(closes) < 25:
        return {"strategy": "EMA18_BREAKOUT", "signal": "INSUFFICIENT_DATA", "actionable": False, "strength": 0}
    ema18 = ema_array(closes, 18)
    curr = closes[-1]
    prev = closes[-2]
    ema_today = ema18[-1]
    ema_yesterday = ema18[-2]
    distance = (curr - ema_today) / ema_today * 100

    if prev < ema_yesterday and curr > ema_today:
        sig, strength = "BUY", 0.8
    elif prev > ema_yesterday and curr < ema_today:
        sig, strength = "SELL", 0.8
    elif curr > ema_today:
        sig, strength = "ABOVE_EMA", min(distance / 5, 0.5)
    else:
        sig, strength = "BELOW_EMA", min(abs(distance) / 5, 0.5)

    return {
        "strategy": "EMA18_BREAKOUT", "signal": sig, "actionable": sig in ("BUY", "SELL"),
        "strength": round(strength, 2), "ema18": round(ema_today, 2),
        "distance_pct": round(distance, 2),
    }


def strategy_gold_impulse(closes):
    if len(closes) < 40:
        return {"strategy": "GOLD_IMPULSE", "signal": "INSUFFICIENT_DATA", "actionable": False, "strength": 0}
    ema13 = ema_array(closes, 13)
    ema12 = ema_array(closes, 12)
    ema26 = ema_array(closes, 26)

    min_len = min(len(ema12), len(ema26))
    macd_line = ema12[-min_len:] - ema26[-min_len:]
    signal_line = ema_array(macd_line, 9)

    if len(signal_line) < 2 or len(ema13) < 2:
        return {"strategy": "GOLD_IMPULSE", "signal": "INSUFFICIENT_DATA", "actionable": False, "strength": 0}

    hist_len = min(len(macd_line), len(signal_line))
    macd_hist = macd_line[-hist_len:] - signal_line[-hist_len:]

    ema_rising = ema13[-1] > ema13[-2]
    ema_falling = ema13[-1] < ema13[-2]
    hist_rising = macd_hist[-1] > macd_hist[-2]
    hist_falling = macd_hist[-1] < macd_hist[-2]

    if ema_rising and hist_rising:
        sig, strength = "BUY", 0.75
    elif ema_falling and hist_falling:
        sig, strength = "SELL", 0.75
    else:
        sig, strength = "NEUTRAL", 0.2

    return {
        "strategy": "GOLD_IMPULSE", "signal": sig, "actionable": sig in ("BUY", "SELL"),
        "strength": round(strength, 2), "macd_hist": round(float(macd_hist[-1]), 4),
    }


def strategy_8020(opens, highs, lows, closes):
    if len(closes) < 3:
        return {"strategy": "STRATEGY_8020", "signal": "INSUFFICIENT_DATA", "actionable": False, "strength": 0}

    body_prev = abs(closes[-2] - opens[-2])
    range_prev = highs[-2] - lows[-2]
    if range_prev == 0:
        return {"strategy": "STRATEGY_8020", "signal": "NO_SETUP", "actionable": False, "strength": 0}
    body_ratio = body_prev / range_prev

    if body_ratio < 0.80:
        return {"strategy": "STRATEGY_8020", "signal": "NO_SETUP", "actionable": False,
                "strength": 0, "body_ratio": round(body_ratio * 100, 1)}

    is_bullish = closes[-2] > opens[-2]
    is_bearish = closes[-2] < opens[-2]

    if is_bullish and closes[-1] < lows[-2]:
        sig, strength = "SELL", 0.85
    elif is_bearish and closes[-1] > highs[-2]:
        sig, strength = "BUY", 0.85
    elif is_bullish:
        sig, strength = "BEARISH_SETUP", 0.5
    elif is_bearish:
        sig, strength = "BULLISH_SETUP", 0.5
    else:
        sig, strength = "SETUP_PENDING", 0.3

    return {
        "strategy": "STRATEGY_8020", "signal": sig, "actionable": sig in ("BUY", "SELL"),
        "strength": round(strength, 2), "body_ratio": round(body_ratio * 100, 1),
    }


def strategy_volume(volumes, closes):
    if len(volumes) < 21:
        return {"strategy": "VOLUME", "signal": "INSUFFICIENT_DATA", "actionable": False, "strength": 0}
    avg_vol = np.mean(volumes[-21:-1])
    today_vol = volumes[-1]
    ratio = today_vol / avg_vol if avg_vol > 0 else 0
    price_change = (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else 0

    if ratio > 2.5 and price_change > 1:
        sig, strength = "BREAKOUT_VOLUME", 0.9
    elif ratio > 2.5 and price_change < -1:
        sig, strength = "SELLOFF_VOLUME", 0.9
    elif ratio > 1.5 and price_change > 0.5:
        sig, strength = "HIGH_BULLISH", 0.6
    elif ratio > 1.5 and price_change < -0.5:
        sig, strength = "HIGH_BEARISH", 0.6
    elif ratio < 0.5:
        sig, strength = "DRY_UP", 0.3
    else:
        sig, strength = "NORMAL", 0.1

    return {
        "strategy": "VOLUME", "signal": sig, "actionable": sig in ("BREAKOUT_VOLUME", "SELLOFF_VOLUME"),
        "strength": round(strength, 2), "vol_ratio": round(ratio, 2),
        "price_change_pct": round(price_change, 2),
    }


def strategy_adx(highs, lows, closes):
    adx, plus_di, minus_di = compute_adx(highs, lows, closes, 14)
    if adx is None:
        return {"strategy": "ADX", "signal": "INSUFFICIENT_DATA", "actionable": False, "strength": 0}

    if adx > 25:
        regime = "TRENDING"
        sig = "TREND_BUY" if plus_di > minus_di else "TREND_SELL"
        strength = min(adx / 50, 1.0)
    elif adx < 20:
        regime = "RANGING"
        sig, strength = "NO_TREND", 0.1
    else:
        regime = "WEAK_TREND"
        sig = "LEAN_BULLISH" if plus_di > minus_di else "LEAN_BEARISH"
        strength = 0.3

    return {
        "strategy": "ADX", "signal": sig, "actionable": sig in ("TREND_BUY", "TREND_SELL"),
        "strength": round(strength, 2), "adx": adx, "plusDI": plus_di, "minusDI": minus_di,
        "regime": regime,
    }


def run_all_strategies(df):
    opens = df["Open"].values
    highs = df["High"].values
    lows = df["Low"].values
    closes = df["Close"].values
    volumes = df["Volume"].values

    results = {
        "momentum_sma": strategy_momentum_sma(closes),
        "ema18_breakout": strategy_ema18(closes),
        "gold_impulse": strategy_gold_impulse(closes),
        "strategy_8020": strategy_8020(opens, highs, lows, closes),
        "volume": strategy_volume(volumes, closes),
        "adx": strategy_adx(highs, lows, closes),
    }

    atr = compute_atr(highs, lows, closes, 14)
    results["_meta"] = {
        "last_price": closes[-1],
        "atr": round(atr, 2) if atr else None,
        "atr_pct": round(atr / closes[-1] * 100, 2) if atr else None,
        "days_of_data": len(closes),
    }

    return results
