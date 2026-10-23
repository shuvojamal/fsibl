# Research round 25: a financial model for the owner's own money (2026-10-24)

**Question.** The owner plans to start with 300–500 USDT. What range of
outcomes should they plan for over 1–5 years, how likely is a loss, and how
deep can the drops get?

Script: `research/scripts/research25.py`. Output: `research/results/research25.out`.

## Method

- **Daily returns:** the live rules on all six close-time versions of
  2018-03 to 2026-10 (round 21's data, 30 coins, costs included), which
  includes round 21's timing luck.
- **Simulation:** 4,000 simulated 5-year paths built from random 30-day
  blocks, so winning and losing streaks stay intact. Balances are read off
  at 1, 2, 3 and 5 years.
- **Scenarios:**
  - *backtest*: returns as tested.
  - *realistic*: 6%/yr less, for live fills, delays, and the survivorship
    and hindsight haircuts from rounds 12, 16 and 21.
  - *half size*: every daily return halved, which is roughly what 0.5% risk
    per trade instead of 1% would give (half the gain and half the swings).
- **Benchmarks:** holding BTC (bootstrapped the same way) and a 4%/yr
  savings rate.

## Results: start with 300 USDT

| Scenario | After | Bad case (5%) | Median | Good case (95%) | Chance of ending below 300 | Typical / bad-case worst drop |
|---|---|---|---|---|---|---|
| backtest | 1 yr | 227 | 352 | 593 | 28% | −20% / −35% |
| backtest | 3 yr | 226 | 501 | 1,195 | 15% | −30% / −49% |
| backtest | 5 yr | 259 | 719 | 2,183 | 8% | −35% / −55% |
| **realistic** | **1 yr** | **215** | **331** | **551** | **37%** | **−22% / −38%** |
| **realistic** | **3 yr** | **188** | **419** | **985** | **26%** | **−33% / −55%** |
| **realistic** | **5 yr** | **187** | **525** | **1,628** | **19%** | **−39% / −62%** |
| half size | 3 yr | 269 | 400 | 609 | 12% | −16% / −28% |
| hold BTC | 3 yr | 98 | 656 | 4,187 | 24% | −62% / −87% |
| savings 4% | 3 yr | 337 | 337 | 337 | 0% | none |

With 50 USDT added every month (realistic): after 3 years, 2,100 put in,
median 2,588, bad case 1,598, 24% chance of being below what was put in.

## What it means

- **Plan around the realistic row:** 300 USDT becomes about **330 after a
  year** and about **420 after three** in the middle case. That's roughly
  +12–15% a year: good, but not life-changing at this size.
- **A losing first year is common:** about 1 chance in 3. The odds improve
  with time (about 1 in 4 at 3 years, 1 in 5 at 5), because the edge needs
  many trades to show.
- **Drops of 20–40% along the way are normal** (bad case 55–60%). Only put
  in money you can watch fall by half without stopping the bot at the
  worst moment.
- **Against holding BTC:** BTC's median is higher (656 vs 501 backtest at
  3 years), but its bad cases are far worse (98 vs 226) and its typical
  drop is −62% against −30%. The bot is the steadier path, not the
  higher-upside one.
- **Half size** (0.5% risk) roughly halves both the gains and the drops,
  and loses money less often. It's a reasonable choice for nervous first
  months with real money.
- **Small capital:** at 300 USDT, a +15% year is about 45 USDT. Adding
  money regularly matters more to the final balance than any strategy
  tweak.

These are model outputs from backtested returns. They aren't promises, and
real trading usually comes in below backtests.
