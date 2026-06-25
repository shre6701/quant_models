"""
Core technical indicators. Single source of truth — all strategies
and backtests import from here. No duplication.
"""

import numpy as np
import pandas as pd


def sma(data, period):
    if len(data) < period:
        return None
    return data[-period:].mean()


def ema_array(data, period):
    if len(data) < period:
        return np.array([])
    k = 2 / (period + 1)
    result = [data[:period].mean()]
    for i in range(period, len(data)):
        result.append(data[i] * k + result[-1] * (1 - k))
    return np.array(result)


def rsi(series, period=2):
    delta = np.diff(series)
    gain = np.where(delta > 0, delta, 0).astype(float)
    loss = np.where(delta < 0, -delta, 0).astype(float)
    k = 1 / period
    ag = pd.Series(gain).ewm(alpha=k, adjust=False).mean().values
    al = pd.Series(loss).ewm(alpha=k, adjust=False).mean().values
    rs = np.where(al > 0, ag / al, 100)
    return 100 - (100 / (1 + rs))


def wilder_smooth(arr, period):
    if len(arr) < period:
        return np.array([])
    val = arr[:period].sum()
    result = [val]
    for i in range(period, len(arr)):
        val = val - val / period + arr[i]
        result.append(val)
    return np.array(result)


def compute_adx(highs, lows, closes, period=14):
    n = len(highs)
    if n < period * 2 + 1:
        return None, None, None

    tr = np.zeros(n)
    plus_dm = np.zeros(n)
    minus_dm = np.zeros(n)

    for i in range(n):
        if i == 0:
            tr[i] = highs[i] - lows[i]
        else:
            tr[i] = max(highs[i] - lows[i],
                        abs(highs[i] - closes[i - 1]),
                        abs(lows[i] - closes[i - 1]))
            up_move = highs[i] - highs[i - 1]
            down_move = lows[i - 1] - lows[i]
            plus_dm[i] = up_move if (up_move > down_move and up_move > 0) else 0
            minus_dm[i] = down_move if (down_move > up_move and down_move > 0) else 0

    s_tr = wilder_smooth(tr, period)
    s_plus = wilder_smooth(plus_dm, period)
    s_minus = wilder_smooth(minus_dm, period)

    dx = []
    plus_di_last = minus_di_last = 0
    for i in range(len(s_tr)):
        plus_di = (s_plus[i] / s_tr[i] * 100) if s_tr[i] > 0 else 0
        minus_di = (s_minus[i] / s_tr[i] * 100) if s_tr[i] > 0 else 0
        total = plus_di + minus_di
        dx.append(abs(plus_di - minus_di) / total * 100 if total > 0 else 0)
        plus_di_last = plus_di
        minus_di_last = minus_di

    adx_arr = wilder_smooth(np.array(dx), period)
    if len(adx_arr) == 0:
        return None, None, None
    return round(adx_arr[-1] / period, 2), round(plus_di_last, 2), round(minus_di_last, 2)


def compute_atr(highs, lows, closes, period=14):
    n = len(highs)
    if n < period + 1:
        return None
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i] - closes[i - 1]))
    atr = wilder_smooth(tr, period)
    return atr[-1] / period if len(atr) > 0 else None
