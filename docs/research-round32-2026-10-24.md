# Research round 32: interest on idle cash

**Question.** With 8 slots at 0.5-1% risk, most of the account sits in
USDT between trades. Binance and OKX both pay interest on USDT in their
flexible savings products ("Simple Earn", withdraw any time). What would
that add?

**Method.** Round 12's simulator on round 21's six close times x two
halves, top 15, 6 checks, 8 slots, steady (0.5%) and growth (1%). The
cash balance earns 2%, 4% or 6% a year as daily compounding interest and
stays available for the next entry.

**Pass bar (set before running).** At 4%, at least +1 point a year on the
2022-26 median return with no deeper median worst drop.

**Result** (`research/results/research32.out`):

- Average share of the account held as cash: steady 80% (2022-26), growth 63%.

| set-up | yield | 2022-26 return/yr | Sharpe | worst drop | gain |
|---|---|---|---|---|---|
| steady | 0% | +15.7% | 1.03 | -16.4% | ref |
| steady | 4% | +19.4% | 1.24 | -14.0% | +3.7 pts |
| growth | 0% | +25.9% | 0.97 | -28.3% | ref |
| growth | 4% | +29.0% | 1.06 | -27.2% | +3.1 pts |

(2% adds about +1.7 points, 6% about +5.)

**Verdict: passes.** It is the first change since round 28 that adds
return without adding market risk. The steady set-up gains the most
because it holds the most cash.

**Caveats.**
- Rates move. Binance's and OKX's flexible USDT rates vary week to week,
  and bonus rates often apply only to small amounts. 2-4% is a fair
  planning range; check the live rate before relying on it.
- The interest is paid by the exchange: it's the same counterparty you
  already trust with the USDT, but it is a separate product with its own terms.
- The demo/testnet accounts have no savings product, so this can't be
  tested there. It only matters for the real account.
- To work, the bot must take USDT out of savings before buying (flexible
  redemption is usually instant) and put spare USDT back after its run.
  That is real-money code against Binance's Simple Earn API; it is not
  built yet and needs the owner's go-ahead.

Simplest way to get it without code: the owner keeps the bot's capital
setting below the account balance and puts the rest in flexible savings
by hand. Note that the bot only sizes trades from its capital setting, so
cash kept in savings has to stay out of that number.
