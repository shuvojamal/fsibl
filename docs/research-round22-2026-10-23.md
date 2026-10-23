# Research round 22: tranching across candle close times (2026-10-23)

**Question.** Round 21 showed that the same rules make +13% to +25% a year
depending only on the UTC hour the daily candle closes, with the live 00:00
close the best of six. A standard defence against timing luck is
tranching: split the capital into equal sub-books, each running the
identical rules on a different close time. Does it help?

Script: `research/scripts/research22.py`. Output: `research/results/research22.out`.
Data and simulator: round 21's (30 coins, daily candles rebuilt from hourly
data, round 12's rules and universe). Each tranche is simulated on its own
(own 5 slots, 1% risk of its own capital), and the tranches are combined
with equal weight, rebalanced daily. Scored 2018-03 to 2026-10.

## Results

| Book | Return/yr | Max DD | Sharpe | Worst 12 months | 2018–21 | 2022–26 |
|---|---|---|---|---|---|---|
| **00:00 alone (live)** | **+25.9%** | −36.2% | 1.05 | −29.7% | +35.4% | **+18.7%** |
| Median single (08:00) | +19.0% | −41.6% | 0.84 | −34.0% | +35.5% | +7.3% |
| 2 tranches (00 + 12) | +20.0% | −39.1% | 0.97 | −32.9% | +33.4% | +10.3% |
| 3 tranches (00 + 08 + 16) | +22.2% | −37.2% | **1.09** | −31.1% | +34.6% | +13.1% |
| 3 tranches without 00:00 | +18.1% | −38.2% | 0.93 | −32.5% | +33.7% | +7.0% |
| 6 tranches (all) | +20.3% | −37.5% | 1.04 | −31.8% | +34.3% | +10.2% |

## What it means

- **Tranching works as insurance.** Against a typical single close time
  (the median), six tranches raise the Sharpe from 0.84 to 1.04 and the
  return from +19% to +20%, with a shallower drawdown and worst year. The
  sub-books' timing noise partly cancels.
- **Against 00:00 alone, it costs return** (about −4 to −6%/yr) for no
  better Sharpe.
- **00:00's lead comes entirely from 2022–26.** In 2018–21 every close time
  made about +34–35%/yr. Since 2022, 00:00 made +18.7% against +7% to +13%
  for the others and for the mixes. That's consistent with the market
  increasingly trading off the "official" daily close that exchanges and
  charts show, but it's one period, so it could still be luck.

## Decision

- No change for now. The bots keep the single 00:00 close.
  - If 00:00's recent advantage is real, tranching would give up about
    5%/yr.
  - If it's luck, 00:00 alone still matches the best mix's Sharpe in this
    test.
- What would change the decision: if the live bots trail the 00:00 backtest
  by much more than costs explain over the coming months, switch to
  3 tranches (00, 08, 16). That's the best Sharpe here (1.09) and keeps
  00:00 in the mix. It would need hourly data, three state folders and runs
  every 8 hours.
