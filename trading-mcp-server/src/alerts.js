const TELEGRAM_API = "https://api.telegram.org/bot";

async function sendTelegramAlert(message) {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;

  if (!token || !chatId) {
    console.error("[ALERT] Telegram not configured — printing to console:");
    console.log(message);
    return { sent: false, reason: "Telegram credentials not configured" };
  }

  const url = `${TELEGRAM_API}${token}/sendMessage`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text: message,
      parse_mode: "Markdown",
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    return { sent: false, reason: err };
  }

  return { sent: true };
}

function formatMomentumAlert(ticker, signal) {
  const emoji = signal.signal === "BUY" ? "🟢" : signal.signal === "SELL" ? "🔴" : "⚪";
  return [
    `${emoji} *MOMENTUM SIGNAL*`,
    `Ticker: \`${ticker}\``,
    `Signal: *${signal.signal}*`,
    `Price: ₹${signal.last_price}`,
    `SMA50: ${signal.fast} | SMA200: ${signal.slow}`,
    `Spread: ${signal.spread_pct}%`,
    `Date: ${signal.date}`,
  ].join("\n");
}

function formatPairAlert(ticker1, ticker2, signal) {
  const emoji = signal.signal === "SHORT_SPREAD" ? "🔵" : signal.signal === "LONG_SPREAD" ? "🟡" : "⚪";
  return [
    `${emoji} *PAIRS SIGNAL*`,
    `Pair: \`${ticker1}\` / \`${ticker2}\``,
    `Signal: *${signal.signal}*`,
    `Z-Score: ${signal.z_score}`,
    `Action: ${signal.action || "None"}`,
    `Date: ${signal.date}`,
  ].join("\n");
}

export { sendTelegramAlert, formatMomentumAlert, formatPairAlert };
