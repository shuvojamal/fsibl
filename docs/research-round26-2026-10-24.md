# Research round 26: hold or trade? Buy-and-hold vs the live rules, coin by coin (2026-10-24)

**Question (from the owner).** Is crypto good to simply hold for the long
term? For each of the 55 coins in round 12's pool: buy and hold from 2018-03
(or the coin's second year of data) until 2026-10, against the live rules
trading that one coin (1% risk per trade, same costs).

Script: `research/scripts/research26.py`. Output: `research/results/research26.out`.
Caveat in holding's favour: the pool is today's list, so coins that died
and were delisted are missing, apart from LUNA, which shows −100%.

## Results

| | Holding | Trend rule, one coin at a time |
|---|---|---|
| Coins that made money | **20 of 55** | **48 of 55** |
| Median result | **−37%** | +22% |
| Lost more than half | 25 of 55 | 0 |
| Median worst drop while held | **−96%** | −11% |
| Smallest worst drop of any coin | −76% (BNB) | — |
| Ended ahead | 17 of 55 | 38 of 55 |
| Smaller worst drop | 0 of 55 | **55 of 55** |

Today, **51 of 55 coins are more than 50% below their all-time high, and 42
are more than 80% below.**

Examples (hold / trend rule): BTC +1,231% / +56%; ETH +762% / +50%; BNB
+7,554% / +99%; SOL +163% / +53%; NEO −78% / +25%; EOS −90% / +6%; IOTA
−90% / +1%; LUNA −100% / −6%.

## What it means

- **Holding works only if you pick the few winners and sit through −75%
  to −95% drops.** BTC, ETH and BNB rewarded patient holders hugely, far
  more than the trend rule on a single coin, which risks only 1% per trade.
  But a typical coin lost money, fell 96% at its worst, and is still far
  below its high.
- **The trend rule wins on survival.** It never had a drop as deep as
  holding on any coin, and it made money on almost all of them, because it
  steps aside when a coin's trend breaks. That's exactly the
  $100 → $1,000 → $50 case: the holder ends at −50%, while the trailing
  stop keeps most of the gain.
- **A sensible split for someone who wants both:** a small long-term
  holding in BTC (and maybe ETH) that you can leave untouched through an
  80% drop, plus the trend bot for the rest. Holding the smaller coins long
  term is closer to a lottery than an investment.
