# Review: PkLavc/Autotrader (2026-10-23)

https://github.com/PkLavc/Autotrader (MIT). Read at the commit cloned on 2026-10-23.

## What it is

- **What it trades:** US stocks, daily, paper-traded with US$10,000 by a
  GitHub Actions job (the same setup as our demo bot).
- **Signal:** the open-source **Kronos** forecasting model
  (github.com/shiyu-coder/Kronos, AAAI 2026, pre-trained on candles from 45+
  exchanges). It predicts each stock's close 5 sessions ahead, ranks the
  forecasts by volatility-adjusted score, and buys up to 5 above +1%. Max
  position 18%, at least 10% cash. Forecasts above +30% are rejected as
  implausible.
- **Good engineering:**
  - Signals at the close fill at the next open (no look-ahead).
  - Each session is processed once, and partial same-day bars are rejected.
  - Splits and dividends are handled.
  - The cost model includes slippage.
  - Broker execution (Alpaca) is separate from the research ledger.
  - Live trading needs several separate opt-ins.
  - There's a state-audit script.
- **Missing:**
  - No historical backtest of the strategy. There is a replay tool, but no
    forecast archive to feed it.
  - No walk-forward results, and no evidence that the Kronos forecasts
    predict anything.

## Its own results so far

The NAV history covers 12 sessions: US$10,000 → US$10,114 (+1.1%), against
its benchmark's −0.8%. That's far too short to mean anything. Twelve days of
a 5-position stock portfolio is noise.

## What's worth taking

1. **The question, not the code.** Kronos was pre-trained on crypto too, so
   it can be tested directly on our coins. That's research round 15
   (`docs/research-round15-2026-10-23.md`). Only data after the model's
   August 2025 release is scored, because the model may have seen anything
   earlier during training.
2. Its safety ideas match what our bot already has (paper by default,
   explicit live gates, signal at close and fill at next open). Two are worth
   copying later: a state-audit script that checks the ledger's invariants
   after each run, and rejecting implausible signals.
