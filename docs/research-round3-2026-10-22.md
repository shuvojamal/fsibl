# Strategy research, round 3 (2026-10-22): exits and sizing

Entry rule held fixed at the round-1 universal setting (5 of 8 checks,
2×ATR initial stop, 1% of equity risked). Daily candles, 10 coins. Each
variant is judged on four test windows *and* the full four years, so it
has to work everywhere, not in one lucky window.

Cells: average return across the 10 coins / number of coins profitable.

| Exit / sizing variant | from 2024-10 | from 2025-03 | from 2025-07 | from 2025-12 | **Full 4 years** | Avg max DD |
|---|---|---|---|---|---|---|
| Baseline: fixed 3:1 target + EMA-cross exit | +0.3% 5/10 | −1.5% 2/10 | +1.2% 8/10 | +1.9% 8/10 | +5.7% 8/10 | −7.4% |
| Trailing stop 2×ATR | +0.4% 5/10 | −0.9% 4/10 | +1.9% 7/10 | +2.4% 8/10 | +8.7% 7/10 | −8.9% |
| **Trailing stop 3×ATR** | +0.4% 6/10 | −0.8% 3/10 | +2.2% 8/10 | +2.5% 7/10 | **+12.4% 9/10** | −10.8% |
| Trailing stop 4×ATR | +0.4% 6/10 | −1.2% 2/10 | +2.2% 8/10 | +2.9% 9/10 | +14.2% 9/10 | −13.0% |
| Trail 3×ATR + keep 3:1 target | +0.8% 6/10 | −0.9% 3/10 | +2.3% 8/10 | +2.3% 7/10 | +6.9% 10/10 | −7.4% |
| Vol-scaled risk (typical ATR 2%) | +0.5% 7/10 | −0.4% 3/10 | +0.9% 8/10 | +1.3% 9/10 | +3.3% 9/10 | −3.2% |
| Vol-scaled risk (typical ATR 3%) | +0.7% 7/10 | −0.6% 3/10 | +1.2% 8/10 | +1.8% 9/10 | +4.9% 9/10 | −4.5% |

## Trailing stop: adopted (3×ATR)

The trailing ("chandelier") stop follows the highest close since entry
minus 3 ATR and is never lowered. It beats or matches the baseline in
every window and more than doubles the full-history return (+5.7% →
+12.4%), profitable on 9 of 10 coins, for a drawdown of −10.8% instead of
−7.4%. 4×ATR earns a little more for noticeably more drawdown; 2×ATR gives
back too much. 3×ATR is the balance.

Where the gain comes from, per coin over the full history:

| Coin | Baseline | Trail 3×ATR | Trades | Win | PF | Max DD | Best single trade |
|---|---|---|---|---|---|---|---|
| BTC | +14.6% | +15.3% | 41 | 37% | 1.53 | −8.3% | +55% |
| ETH | +9.1% | +6.1% | 36 | 36% | 1.33 | −9.7% | +49% |
| SOL | +9.7% | **+37.5%** | 34 | 32% | 2.13 | −13.4% | **+371%** |
| XRP | +6.9% | **+33.7%** | 38 | 29% | 1.80 | −15.7% | **+286%** |
| DOGE | −0.1% | +10.8% | 29 | 34% | 1.48 | −9.5% | +137% |
| ADA | +5.4% | +8.1% | 28 | 25% | 1.09 | −9.8% | +108% |
| LINK | +7.2% | +5.0% | 32 | 31% | 1.14 | −10.6% | +78% |
| AVAX | +5.6% | +10.6% | 25 | 32% | 1.58 | −9.3% | +147% |
| DOT | +2.0% | +2.8% | 25 | 28% | 0.84 | −11.7% | +85% |
| LTC | −3.8% | −5.9% | 40 | 25% | 0.52 | −10.1% | +39% |

This is textbook trend-following arithmetic: the win rate drops to about
30% (the trail gives back open profit on most trades), but a few trades
run for +100% to +370% and pay for everything. The baseline capped every
winner at three times its risk and never caught those. Two consequences
for whoever runs it:

- **Most trades will lose.** Seven out of ten, roughly. That is the design,
  not a malfunction, and it is hard to sit through.
- **The returns depend on bull runs happening.** In a sideways or falling
  year it earns little or loses a little (see the 2025-03 window).

## Volatility-scaled risk: not adopted

Risking less when ATR is high lowers both return and drawdown in the same
proportion (+3.3% with −3.2% DD vs +5.7% with −7.4%). It is a dial, not
an edge; the same effect comes from a smaller `--risk`.

## Overall standing after three rounds

Trailing-stop scorer, 1% risk per trade, full history: **+12.4% over four
years, about +3% a year, 9 of 10 coins, worst drawdown −16%.** Scaling to
2% risk roughly doubles both. Still far behind buy-and-hold in a bull
market (BTC +15% vs +275%), and still with long idle stretches (no
entries on any coin since 2026-05-25). What it offers is a positive
expectancy at a drawdown most people can live with.

## Next

- Run the trailing version on the OKX demo (it is now the default).
- Research round 4 candidates: pyramiding into a working trend (adding
  size as the trail rises); a portfolio cap on simultaneous open positions;
  the short side on futures (demo only) for bear markets.
