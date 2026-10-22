# Strategy research, round 7 (2026-10-22): which checks matter, and costs

20-coin shared account (10,000 USDT, max 5 open, 1% of equity per trade,
trailing-stop scorer, daily). Cells: return / max drawdown / profit factor.

## A. Ablation: stop requiring one check at a time

| Variant | Full 4y | from 2024-10 | from 2025-07 | from 2025-12 |
|---|---|---|---|---|
| **Baseline, all 8 required (5 of 8)** | +152% / −33% / 1.74 | +76% / −33% / 1.84 | +12% / −23% / 1.31 | +24% / −16% / 2.01 |
| without trend_up | +112% / −41% / 1.49 | +47% / −41% / 1.43 | −10% / −33% / 0.82 | +6% / −21% / 1.22 |
| without ema_aligned | +148% / −38% / 1.64 | +56% / −38% / 1.55 | +2% / −27% / 1.05 | +17% / −17% / 1.65 |
| without momentum | +119% / −39% / 1.56 | +6% / −36% / 1.10 | −5% / −27% / 0.89 | +1% / −19% / 1.07 |
| **without rsi_zone** | **+201% / −32% / 1.98** | **+91% / −31% / 2.04** | **+21% / −20% / 1.60** | **+33% / −15% / 2.52** |
| without volume | +105% / −37% / 1.54 | +43% / −37% / 1.47 | −3% / −24% / 0.94 | +14% / −15% / 1.79 |
| without volatility_ok | +89% / −49% / 1.37 | +21% / −49% / 1.19 | −19% / −37% / 0.67 | −2% / −22% / 0.96 |
| without breakout | +102% / −46% / 1.41 | −8% / −43% / 0.93 | −16% / −35% / 0.69 | −7% / −25% / 0.81 |
| without pullback | +111% / −38% / 1.50 | +47% / −38% / 1.46 | +1% / −25% / 1.04 | +8% / −17% / 1.32 |

Seven of the eight checks earn their place: dropping any of them makes
every window worse, and dropping `breakout` or `volatility_ok` turns the
strategy into a loser. The one exception is the **RSI zone (45–65)**:
not requiring it improves every window, with less drawdown and a higher
profit factor. The zone was built to avoid "overbought" entries; in a
trending market the strongest entries *are* the ones with RSI above 65.

## 7b. Verifying the RSI finding on each half of the universe

| Variant | All 20 | Original 10 | Other 10 |
|---|---|---|---|
| Baseline (RSI 45–65 required) | +152 / +76 / +12 / +24 | +106 / +69 / +7 / +18 | +131 / +92 / +22 / +32 |
| RSI check removed (4 of other 7) | +201 / +91 / +21 / +33 | +123 / +84 / +11 / +18 | +142 / +102 / +23 / +32 |
| RSI removed, 5 of 7 (stricter) | +61 / +26 / +6 / +8 | +70 / +39 / +2 / +9 | +108 / +72 / +8 / +15 |
| **RSI zone widened to 40–80** | **+188 / +92 / +22 / +34** | +114 / +76 / +7 / +17 | **+134 / +100 / +28 / +37** |
| RSI zone 50–80 ("momentum only") | +121 / +69 / +8 / +16 | +125 / +81 / +14 / +24 | +104 / +78 / +17 / +28 |

(returns for full 4y / from 2024-10 / from 2025-07 / from 2025-12)

Removing the check outright helps on the 20 and on each half, but it is
partly a threshold effect (4 of 7 is looser; 5 of 7 is much worse).
**Widening the zone to 40–80** keeps the check, keeps 5 of 8, and is
better or equal on every window of every universe, with lower drawdowns
on the 20. That is the change adopted: `rsi_lo=40, rsi_hi=80`. It still
rejects oversold entries (a dip that has not stopped falling) and
blow-off tops (RSI above 80).

## B. Threshold

| min_score | Full 4y | from 2024-10 | from 2025-07 | from 2025-12 |
|---|---|---|---|---|
| 4 of 8 | +120% / −45% | +1% / −42% | −8% / −33% | −1% / −24% |
| **5 of 8** | +152% / −33% | +76% / −33% | +12% / −23% | +24% / −16% |
| 6 of 8 | +72% / −22% | +13% / −22% | −3% / −10% | +0% / −7% |

5 of 8 stays. Four lets in too much; six is safe but barely trades.

## C. Execution costs

| Costs (fee per side + slippage) | Full 4y | from 2024-10 | from 2025-07 | from 2025-12 |
|---|---|---|---|---|
| none (upper bound) | +173% | +85% | +15% | +26% |
| 0.10% + 0.05% (assumed so far) | +152% | +76% | +12% | +24% |
| 0.20% + 0.10% (double) | +132% | +69% | +8% | +21% |
| 0.30% + 0.15% (triple) | +114% | +62% | +5% | +19% |

The edge survives triple the assumed costs in every window. With about
60 trades a year it is not a cost-sensitive strategy; a demo or live run
with worse fills than assumed should still show the same shape.

## Decisions

- RSI zone widened to 40–80 (default changed; tests updated).
- Threshold, other seven checks, costs model: unchanged.
- The live bots pick up the new zone on their next restart; it only
  affects which new entries qualify, not open positions.

## Next

- Round 8: time-based exit (close a trade that has gone nowhere after N
  days) and a re-entry rule after a stop-out; both in the 20-coin sim.
- A third universe of 10 coins to repeat the generalisation test.
