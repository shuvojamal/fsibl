# Research round 20: a short side for bear markets (2026-10-23)

**Question.** The bot only buys, and it lost money in 2018 (−14%), 2022
(−28%) and 2025 (−11%). Perpetual futures let a bot short a coin and profit
when it falls. Does a mirror image of the live rules make money on the
short side, and does it smooth out the bad years?

Script: `research/scripts/research20.py`. Output: `research/results/research20.out`.
The short rules are the live rules applied to the inverted price, so every
check flips: price below a falling 200-EMA, a close below the 20-day low,
and so on. Stop 2×ATR above, trailing 3×ATR above the lowest close, 1%
risk, sharing the same 5 slots with the longs. Costs as round 12, plus real
funding (round 13's data) received or paid on shorts, and 1:1 collateral
(no leverage). With longs only, the simulator reproduces round 12 exactly
(+22.67%/yr, 487 trades).

## Results

| | 2017–26 | Max DD | 2017–21 | 2022–26 |
|---|---|---|---|---|
| **Longs only (live)** | **+22.7%/yr, Sh 0.97** | **−31%** | +26.9% | +19.3% |
| Shorts only | −5.0%/yr | −64% | −6.4% | −3.5% |
| Shorts only, BTC below 200-EMA | −1.7%/yr | −50% | −1.1% | −2.0% |
| Longs + shorts | +23.5%/yr, Sh 1.00 | −30% | +39.5% | **+10.7%** |
| Longs + shorts (shorts only in BTC bear) | +21.9%/yr, Sh 0.91 | −36% | +34.0% | +12.0% |

Shorts by year (shorts only): 2018 **+31%**, 2022 **+33%**, but 2019 −12%,
2020 −22%, 2021 −16%, 2023 −33%, 2024 −17%. Short trades averaged −0.08R
(longs: +0.46R).

## What it means

- **Mirrored shorts lose money.** They pay off in true crashes (2018, 2022)
  but bleed in every other year. Crypto drifts upward over time and its
  rallies are violent, so short trades get stopped out in squeezes far more
  often than long trades get stopped in crashes. Even restricted to bear
  markets (BTC below its 200-EMA), they're negative in both halves.
- **Adding them to the book doesn't hold up.** The whole-period total looks
  slightly better (+23.5% vs +22.7%), but only because of 2017–21. In
  2022–26 the combined book made +10.7%/yr against +19.3% for longs only.
  2022 improved from −28% to −6%, but 2023 fell from +77% to +17% and 2024
  from +33% to +10%. Short trades took slots that long winners would have
  used.
- **Funding didn't help.** Shorts tend to open when funding has turned
  negative (bear markets), so they paid it on balance.
- The bot already defends against bear markets by holding cash: its checks
  stop signalling, and the stops get it out. That costs far less than
  fighting the trend from the short side.

## Decision

Rejected. The bot stays long-only.
