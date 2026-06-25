import { multiScan } from './src/strategies.js';
import { readFileSync } from 'fs';

const data = JSON.parse(readFileSync('./scan_input.json', 'utf-8'));
const stocks = data.map(({ ticker, candles }) => ({
  ticker,
  opens: candles.map(c => c.open),
  highs: candles.map(c => c.high),
  lows: candles.map(c => c.low),
  closes: candles.map(c => c.close),
  volumes: candles.map(c => c.volume),
}));

const result = multiScan(stocks);

console.log(`\n=== MULTI-STRATEGY SCAN (${result.summary.total_scanned} stocks) ===`);
console.log(`Actionable: ${result.summary.actionable_count}`);
console.log(`Regime: Trending=${result.summary.regime_breakdown.trending}, Ranging=${result.summary.regime_breakdown.ranging}, Weak=${result.summary.regime_breakdown.weak}`);

if (result.actionable.length > 0) {
  console.log('\n--- ACTIONABLE SIGNALS ---');
  for (const s of result.actionable) {
    console.log(`\n${s.ticker} (score: ${s.priority_score}, price: ${s.last_price})`);
    for (const a of s.actionable) {
      console.log(`  >> ${a.strategy}: ${a.signal}`);
    }
  }
}

console.log('\n--- ALL STOCKS SUMMARY ---');
for (const s of result.all) {
  const signals = Object.entries(s.signals)
    .map(([k, v]) => `${k}:${v.signal}`)
    .join(' | ');
  console.log(`${s.ticker.padEnd(12)} P:${s.priority_score.toString().padStart(2)} | ${signals}`);
}

console.log('\n--- DETAILED SIGNALS ---');
for (const s of result.all) {
  console.log(`\n${s.ticker} (${s.last_price}):`);
  for (const [k, v] of Object.entries(s.signals)) {
    console.log(`  ${k}: ${JSON.stringify(v)}`);
  }
}
