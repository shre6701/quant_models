"""
Trade recommendation engine.

Takes strategy signals + backtest stats and outputs:
  - Direction: LONG / SHORT
  - Timeframe: POSITIONAL / SWING / SCALPING
  - Or: NO TRADE

Decision matrix:
  POSITIONAL (hold weeks)  = Strong trend (ADX>30) + 3+ confirming signals + positive backtest
  SWING (hold days)        = Trending + 2+ signals + positive backtest
  SCALPING (intraday)      = Volume spike (>2.5x) + momentum + tight ATR
  NO TRADE                 = No confluence / no backtest edge / conflicting signals
"""


BULLISH_SIGNALS = {"BUY", "TREND_BUY", "BULLISH_SETUP", "BREAKOUT_VOLUME", "HIGH_BULLISH"}
BEARISH_SIGNALS = {"SELL", "TREND_SELL", "BEARISH_SETUP", "SELLOFF_VOLUME", "HIGH_BEARISH"}


def classify_trade(signals, backtest_result, mc_stats):
    """
    Args:
        signals: dict from run_all_strategies()
        backtest_result: tuple (total_ret, max_dd, win_rate, trade_count, avg_hold, trades)
        mc_stats: dict from bootstrap_mc() or None
    Returns:
        (trade_type: str, confidence: int 0-100, reason: str, risk_notes: str)
    """
    total_ret, max_dd, win_rate, trade_count, avg_hold, _ = backtest_result

    buy_score = 0.0
    sell_score = 0.0
    actionable_count = 0

    for name, s in signals.items():
        if name == "_meta":
            continue
        if not s.get("actionable"):
            continue
        actionable_count += 1
        strength = s.get("strength", 0.5)
        if s["signal"] in BULLISH_SIGNALS:
            buy_score += strength
        elif s["signal"] in BEARISH_SIGNALS:
            sell_score += strength

    # Direction
    if buy_score > sell_score and buy_score > 0:
        direction = "LONG"
        dir_score = buy_score
    elif sell_score > buy_score and sell_score > 0:
        direction = "SHORT"
        dir_score = sell_score
    else:
        return "NO TRADE", 0, "No clear directional confluence", ""

    # Edge validation
    has_edge = total_ret > 0 and win_rate > 45
    if mc_stats:
        has_edge = has_edge and mc_stats["p_loss"] < 45

    if not has_edge and actionable_count < 3:
        risk = f"BT: {total_ret:.1f}% ret, {win_rate:.0f}% WR"
        if mc_stats:
            risk += f", {mc_stats['p_loss']:.0f}% loss prob"
        return "NO TRADE", 0, f"Backtest shows weak/no edge", risk

    # Regime and volatility context
    adx_data = signals.get("adx", {})
    adx_val = adx_data.get("adx") or 0
    regime = adx_data.get("regime", "UNKNOWN")
    vol_data = signals.get("volume", {})
    vol_ratio = vol_data.get("vol_ratio") or 1
    meta = signals.get("_meta", {})
    atr_pct = meta.get("atr_pct") or 2

    # Confidence: weighted sum of signal strengths + confirmations
    confidence = int(min(100, dir_score * 25 + (15 if adx_val > 25 else 0) + (10 if vol_ratio > 1.5 else 0)))

    # Timeframe classification
    if regime == "TRENDING" and adx_val > 30 and actionable_count >= 3:
        trade_type = f"POSITIONAL {direction}"
        reason = f"Strong trend ADX={adx_val}, {actionable_count} confirming signals"
    elif regime == "TRENDING" and actionable_count >= 2:
        trade_type = f"SWING {direction}"
        reason = f"Trending ADX={adx_val}, {actionable_count} signals aligned"
    elif vol_ratio > 2.5 and actionable_count >= 2 and atr_pct < 3:
        trade_type = f"SCALPING {direction}"
        reason = f"Volume spike {vol_ratio:.1f}x + tight range (ATR {atr_pct:.1f}%)"
    elif vol_ratio > 2.5 and actionable_count >= 2:
        trade_type = f"SWING {direction}"
        reason = f"Volume spike {vol_ratio:.1f}x with {actionable_count} signals"
    elif actionable_count >= 2:
        trade_type = f"SWING {direction}"
        reason = f"{actionable_count} signals aligned, moderate conviction"
    elif actionable_count == 1 and has_edge:
        trade_type = f"SWING {direction}"
        reason = "Single signal, reduce size"
        confidence = max(confidence - 20, 10)
    else:
        return "NO TRADE", 0, "Insufficient confluence", ""

    # Risk notes
    risk_parts = []
    if max_dd < -15:
        risk_parts.append(f"DD risk: {max_dd:.0f}%")
    if mc_stats and mc_stats["worst5_dd"] < -20:
        risk_parts.append(f"MC worst-5% DD: {mc_stats['worst5_dd']:.0f}%")
    if atr_pct > 3:
        risk_parts.append(f"High volatility: ATR {atr_pct:.1f}%")
    risk_notes = " | ".join(risk_parts)

    return trade_type, confidence, reason, risk_notes


def position_size(capital, price, atr, risk_pct=1.0, atr_multiplier=2.0):
    """
    ATR-based position sizing.
    Risk risk_pct% of capital per trade, stop at atr_multiplier * ATR.
    """
    if not atr or atr <= 0:
        return 0, 0
    risk_amount = capital * (risk_pct / 100)
    stop_distance = atr * atr_multiplier
    shares = int(risk_amount / stop_distance)
    stop_loss = price - stop_distance
    return shares, round(stop_loss, 2)
