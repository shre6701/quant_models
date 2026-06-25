# Graph Report - .  (2026-06-25)

## Corpus Check
- Corpus is ~14,130 words - fits in a single context window. You may not need a graph.

## Summary
- 193 nodes · 280 edges · 15 communities (11 shown, 4 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 20 edges (avg confidence: 0.81)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_MCP Signal Scanner|MCP Signal Scanner]]
- [[_COMMUNITY_Daily Analysis Pipeline|Daily Analysis Pipeline]]
- [[_COMMUNITY_Batch Backtester|Batch Backtester]]
- [[_COMMUNITY_JS Strategy Engine|JS Strategy Engine]]
- [[_COMMUNITY_Core Indicators|Core Indicators]]
- [[_COMMUNITY_Monte Carlo & Risk|Monte Carlo & Risk]]
- [[_COMMUNITY_README Documentation|README Documentation]]
- [[_COMMUNITY_Alerts & MCP Server|Alerts & MCP Server]]
- [[_COMMUNITY_Package Dependencies|Package Dependencies]]
- [[_COMMUNITY_Aegis Terminal Scanner|Aegis Terminal Scanner]]
- [[_COMMUNITY_Forward Simulator|Forward Simulator]]
- [[_COMMUNITY_ML Prediction Models|ML Prediction Models]]
- [[_COMMUNITY_Risk Attribution|Risk Attribution]]
- [[_COMMUNITY_Decision Engine|Decision Engine]]
- [[_COMMUNITY_Project Overview|Project Overview]]

## God Nodes (most connected - your core abstractions)
1. `run_all_strategies()` - 11 edges
2. `Multi-Strategy Scanner` - 10 edges
3. `Trading-Signals MCP Server` - 10 edges
4. `8-Layer Composite Scoring System` - 9 edges
5. `analyze_ticker()` - 8 edges
6. `scanStock()` - 8 edges
7. `Monte Carlo Simulation Engine (Guide)` - 7 edges
8. `r2()` - 7 edges
9. `forward_sim()` - 6 edges
10. `forward_sim()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Synthetic Data Generator (forward_montecarlo)` --semantically_similar_to--> `Geometric Brownian Motion (GBM) Formula`  [INFERRED] [semantically similar]
  forward_and_montecarlo.py → Quant Finance Master Prompt Guide Deepkumar Khinchi-merged-.pdf
- `rsi()` --semantically_similar_to--> `Mean Reversion Signal Engine (Guide)`  [INFERRED] [semantically similar]
  batch_test.py → Quant Finance Master Prompt Guide Deepkumar Khinchi-merged-.pdf
- `Forward Simulator (Walk-Forward)` --semantically_similar_to--> `Market Timing Optimization Model`  [INFERRED] [semantically similar]
  forward_and_montecarlo.py → Quant Finance Master Prompt Guide Deepkumar Khinchi-merged-.pdf
- `Monte Carlo on Strategy Trades` --semantically_similar_to--> `Monte Carlo Simulation Engine (Guide)`  [INFERRED] [semantically similar]
  forward_and_montecarlo.py → Quant Finance Master Prompt Guide Deepkumar Khinchi-merged-.pdf
- `bootstrap()` --semantically_similar_to--> `Bootstrap (Resampling) Method`  [INFERRED] [semantically similar]
  batch_test.py → forward_and_montecarlo.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Decision Engine Pipeline (Strategies + Backtest + Monte Carlo -> Recommendation)** — readme_engine_strategies, readme_engine_backtest, readme_engine_recommendation, readme_decision_engine, readme_gating_rules [EXTRACTED 1.00]
- **Six Strategy Scanner (Momentum + EMA18 + Gold Impulse + 80/20 + Volume + ADX)** — scan_guide_momentum_sma, scan_guide_ema18_breakout, scan_guide_gold_impulse, scan_guide_8020_okala, scan_guide_volume_spike, scan_guide_adx_trend [EXTRACTED 1.00]
- **Dual MCP Architecture (Kite Data + Trading-Signals Compute + Telegram Alerts)** — usage_kite_mcp, usage_trading_signals_mcp, usage_telegram_alerts, usage_architecture [EXTRACTED 1.00]

## Communities (15 total, 4 thin omitted)

### Community 0 - "MCP Signal Scanner"
Cohesion: 0.08
Nodes (29): MCP Telegram Notifications, MCP Tool Registration (index.js), MCP Market Data Signals, Trading MCP Server, 80/20 Okala Strategy, ADX Trend Strategy, 18 EMA Breakout Strategy, Gold Impulse Strategy (Elder) (+21 more)

### Community 1 - "Daily Analysis Pipeline"
Cohesion: 0.16
Nodes (19): analyze_ticker(), main(), daily_analysis.py — Daily Trading Decision System ==============================, read_watchlist(), write_output(), bootstrap_mc(), forward_sim(), Walk-forward backtest + Monte Carlo bootstrap. Identical logic to batch_test.py (+11 more)

### Community 2 - "Batch Backtester"
Cohesion: 0.13
Nodes (21): bootstrap(), cost(), forward_sim(), load_ticker(), main(), make_synthetic(), Overfitting Warning Rationale, batch_test.py ============= Run the RSI-2 mean-reversion strategy across MANY ti (+13 more)

### Community 3 - "JS Strategy Engine"
Cohesion: 0.21
Nodes (17): adxStrategy(), computeADX(), ema18Breakout(), emaArray(), goldImpulse(), momentumSignal(), multiScan(), r2() (+9 more)

### Community 4 - "Core Indicators"
Cohesion: 0.27
Nodes (14): compute_adx(), compute_atr(), ema_array(), Core technical indicators. Single source of truth — all strategies and backtests, sma(), wilder_smooth(), Six-strategy signal scanner. Each strategy returns a standardized dict:   {signa, run_all_strategies() (+6 more)

### Community 5 - "Monte Carlo & Risk"
Cohesion: 0.14
Nodes (15): Bootstrap (Resampling) Method, Monte Carlo on Strategy Trades, Reshuffle (Permutation) Method, Rationale: Reshuffle vs Bootstrap Distinction, Black-Scholes Options Pricing Engine, Blended Volatility (VIX + Historical), Cholesky Decomposition for Correlated MC, Deepkumar Khinchi (@deepthinksfinance) (+7 more)

### Community 6 - "README Documentation"
Cohesion: 0.14
Nodes (15): Analysis Output (analysis_output.xlsx), Batch Backtest Runner, Confidence Score System, Daily Analysis Entry Point, Walk-Forward Backtest + Monte Carlo, Data Fetching Module (Yahoo Finance), Technical Indicators Module, Decision Engine + Position Sizing (+7 more)

### Community 7 - "Alerts & MCP Server"
Cohesion: 0.26
Nodes (10): formatMomentumAlert(), formatPairAlert(), sendTelegramAlert(), server, transport, computeMomentumSignal(), computePairSignal(), computeRegime() (+2 more)

### Community 8 - "Package Dependencies"
Cohesion: 0.15
Nodes (12): dependencies, dotenv, @modelcontextprotocol/sdk, zod, description, main, name, scripts (+4 more)

### Community 9 - "Aegis Terminal Scanner"
Cohesion: 0.22
Nodes (11): 8-Layer Composite Scoring System, Alternative Data Layer, Altman Z-Score Model, Beneish M-Score Model, AEGIS Forensic Equity Terminal, Corporate Governance Layer, Insider Trading Analysis Layer, Piotroski F-Score Model (+3 more)

### Community 10 - "Forward Simulator"
Cohesion: 0.24
Nodes (7): cost_fraction_per_side(), forward_simulate(), monte_carlo_trades(), forward_and_montecarlo.py =========================  TWO honest tools that fit y, trade_returns_pct: list/Series of per-trade % returns (e.g. tr['ret_pct'])., Simulate trading the RSI-2 rule forward. On day i we compute indicators     usin, rsi()

## Knowledge Gaps
- **54 isolated node(s):** `Overfitting Warning Rationale`, `Insider Trading Analysis Layer`, `Corporate Governance Layer`, `Valuation Analysis Layer`, `Alternative Data Layer` (+49 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Value at Risk (VaR) Dashboard` connect `Monte Carlo & Risk` to `Aegis Terminal Scanner`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `Altman Z-Score Model` connect `Aegis Terminal Scanner` to `Monte Carlo & Risk`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **What connects `batch_test.py ============= Run the RSI-2 mean-reversion strategy across MANY ti`, `Different seed per ticker so synthetic stocks aren't identical.`, `forward_and_montecarlo.py =========================  TWO honest tools that fit y` to the rest of the system?**
  _69 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `MCP Signal Scanner` be split into smaller, more focused modules?**
  _Cohesion score 0.07635467980295567 - nodes in this community are weakly interconnected._
- **Should `Batch Backtester` be split into smaller, more focused modules?**
  _Cohesion score 0.12987012987012986 - nodes in this community are weakly interconnected._
- **Should `Monte Carlo & Risk` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Should `README Documentation` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._