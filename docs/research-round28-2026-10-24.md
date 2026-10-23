# Research round 28: portfolio sizing, max positions × risk per trade (2026-10-24)

**Question.** The two app settings that shape results most are how many
positions may be open at once and how much each trade risks. Round 16
hinted that 8 slots beat 5. This round tests max positions 3/5/8/10 × risk
0.5/1/1.5% on round 21's six close times × two halves (12 cells).

**Pass bar, set before running:** recommend a combination over the live
one (5 slots, 1%) only if it has the higher Sharpe in at least 9 of 12
cells **and** its median 2022–26 drawdown is no more than 5 points deeper.

Script: `research/scripts/research28.py`. Output: `research/results/research28.out`.

## Results (median over six close times)

| Slots | Risk | 2018–21 | 2022–26 | Drawdown 22–26 | Sharpe wins vs live | Verdict |
|---|---|---|---|---|---|---|
| 3 | 1% | +21.4%, Sh 1.24 | +4.7%, 0.38 | −23.0% | 2/12 | |
| **5** | **1%** | **+35.2%, 1.28** | **+10.8%, 0.54** | **−30.4%** | — | **live** |
| 5 | 0.5% | +18.0%, 1.27 | +6.5%, 0.55 | −16.3% | 6/12 | |
| **8** | **0.5%** | **+30.7%, 1.46** | **+13.5%, 0.76** | **−21.7%** | **12/12** | **PASS** |
| 8 | 1% | +60.9%, 1.51 | +16.9%, 0.63 | −39.5% | 10/12 | drawdown too deep |
| 10 | 0.5% | +37.5%, 1.51 | +14.7%, 0.74 | −25.4% | 12/12 | PASS |
| 10 | 1% | +75.3%, 1.56 | +14.4%, 0.55 | −41.9% | 10/12 | drawdown too deep |
| any | 1.5% | | | −45% to −53% | ≤ 8/12 | |

## What it means

- **Spreading the same risk over more, smaller positions works better.** 8
  slots at 0.5% put at most 4% of the account at risk at once (live: 5%).
  Yet it made **more** in the recent half (+13.5% vs +10.8%/yr), with a
  much **shallower worst drop** (−21.7% vs −30.4%) and the better Sharpe in
  all 12 cells. With 5 slots, the bot often has to skip good signals
  because it's full; with 8 smaller ones it catches more trends without
  betting more.
- **More risk per trade isn't worth it.** 1.5% raised returns in the bull
  half but deepened drawdowns to −45% to −53%, and lowered the recent
  Sharpe.
- **3 slots is too few** at any risk level.
- **For 300 USDT:** 0.5% risk is $1.50 per trade, so positions are about
  $15–75. That's still above Binance's $5 minimum order and OKX's $1, and
  fees are included in the test.

## Recommendation (the owner decides; nothing was changed)

Set **Max positions 8** and **Risk per trade 0.5%** on both test accounts,
in the app under Edit settings. It's the first sizing change that passes a
pre-set bar in all 12 cells. Applying it to both accounts keeps the 5-vs-6
checks comparison clean. It's also a good fit for the real account's
nervous first months: smaller bets, more of them, shallower drops.
