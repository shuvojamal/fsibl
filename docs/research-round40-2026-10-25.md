# Research round 40: slow quarterly investing on DSE

**Question.** Round 38 rejected daily trend trading on DSE. Does a slow,
quarterly approach (hold good shares for months, collect bonus shares and
capital gains) work instead? And how common is the 30%-a-year share?

**Data.** Round 38's adjusted DSE prices (Mendeley doi:10.17632/23553sm4tn.4,
CC BY 4.0), 2012-10 .. 2026-01. Adjusted for bonus shares and splits, **not
for cash dividends** (checked on GP, a cash-only payer). Returns below are
price + bonus; real returns would be higher by the dividend yield (often
3-6%/yr). DSEX, the benchmark, is a price index with the same omission.

**Method.** Rebalance on the first trading day of each quarter at the open,
using data up to the previous close. Universe: the 50 most-traded liquid
equities. Equal weight, costs 0.7% per side. Strategies: 12-1 momentum
(primary, top 10), top 5/20, 6-month momentum, low volatility, momentum +
low volatility, momentum with a DSEX trend filter; benchmarks: holding DSEX
and an equal-weight basket of all 50. Halves 2013-10..2019 and 2020..2026-01.
Pass bar (set first): the primary must beat DSEX and the equal-weight basket
in both halves with a worst drop within 5 points of DSEX's.

**Result** (`research/results/research40.out`, yearly return, price + bonus):

| strategy | 2013-10..2019 | 2020..2026-01 |
|---|---|---|
| momentum 12-1, top 10 (primary) | −4.9% | −10.0% |
| momentum 6 months | −3.1% | +1.2% |
| momentum + low volatility | −3.8% | +0.9% |
| low volatility | −7.6% | −5.7% |
| momentum + DSEX filter | −8.6% | −1.5% |
| equal-weight 50 most-traded | −9.1% | −5.0% |
| **hold DSEX** | **+2.1%** | **+2.4%** |

Verdict: **fails**; no variant beat both benchmarks in both halves.

**The 30%-a-year shares** (price + bonus, to Jan 2026): over 5 years, 6 of
327 shares (2%) did it: FINEFOODS +52%, HAMI +42%, ORIONINFU +41%, KBPPWBIL
+41%, GQBALLPEN +35%, AL-HAJTEX +31%. Over 10 years, 5 of 280 (2%):
FINEFOODS +49%, ZEALBANGLA, SHYAMPSUG, KAY&QUE +35%, DULAMIACOT +33%. The
median share made −5.4%/yr over 5 years and −0.3%/yr over 10. Such shares
exist, but they are rare, mostly small, and no rule tested here found them
in advance; momentum, which should catch risers, lost money.

**What it means.** On DSE the broad market has been weak and the most-traded
shares worse; the large companies that dominate DSEX did better. A signal
service built on these rules would have lost money, so none is built.
Untested and possibly better: holding a few large, steady dividend payers
(needs dividend records, which this data lacks).
