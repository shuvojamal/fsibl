# Research round 66: how long does the bot normally sit with no positions? (scheduled daily run)

**Prompt.** The VPS testnet has held nothing since 2026-11-13 and had no buy
signal for five days; the owner has asked before why the bot isn't buying.

**Method.** Daily count of open positions, steady set-up, round 12's
simulator, round 21's six close times, 2018-26. Pass bar (set first): a
5-day flat spell is "normal" if at least 25% of flat spells last 5+ days.

**Result** (`research/results/research66.out`):
- The account holds **no positions on 35% of days**; 1-3 positions 31%,
  4-7 positions 20%, all 8 slots full 14%.
- Flat spells: median **13 days**; a quarter last 24+ days; 1 in 10 lasts
  49+ days; the longest was 191 days (a bear market).
- 75% of flat spells last 5 days or more.

**Verdict: normal.** Sitting in cash is a large part of how this strategy
works: it only buys when 6 of 8 checks agree, which in weak or choppy
markets can take weeks. Long flat spells are also what protects the
account in bear markets.

**Meaning for the owner:** days or weeks with no buys are expected, not a
fault. While the account is flat, auto savings (round 32) would earn
interest on the idle USDT on the real account.
