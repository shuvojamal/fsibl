# Research round 59: how far past the stop do losing exits land? (scheduled daily run)

**Prompt.** Stops act at the daily close and sell at the next open, so a
losing exit usually fills below the stop: ZEC on 2026-11-11 sold at 1042.95
against a 1062.46 stop; TRX on 2026-10-31 at 0.3248 against 0.3352.

**Method.** Every losing trade of the steady set-up, round 12's simulator,
round 21's six close times, 2018-26 (1,504 losers), in R (multiples of the
planned initial risk). Pass bar (set first): median loser no worse than
−1.1R and fewer than 5% of losers worse than −1.5R.

**Result** (`research/results/research59.out`): median −0.85R (many losers
had a raised trail); 10% worse than −1.31R; 14.8% worse than −1.2R; **5.7%
worse than −1.5R**; 1.8% worse than −2R; worst −2.75R.

**Verdict: fails narrowly** (5.7% vs the 5% bar). About one losing trade in
17 costs 1.5× its planned risk or more, from gaps and big days between the
close that breaches the stop and the next open.

**Meaning.** This is the known cost of daily-close stops. Round 19 found
resting exchange stop orders at the stop level do worse overall (normal
intraday swings trigger them), so no change. For planning: an individual
stop-out can cost up to about 2-3× the planned 0.5-1%; the backstop (20%
below the stop) only guards against much larger crashes (round 49).

**Also today (bug fixes, both with tests):**
- `round_qty` (Binance and OKX clients) used `floor(qty / step)`, and float
  error (0.206 / 0.001 = 205.999...) dropped a whole lot step in about
  2,250 ordinary quantities; the testnet sold 0.205 of 0.206 ZEC and left
  0.001 behind. A tiny tolerance fixes it; it still never rounds up.
- The audit flagged that leftover. It now accepts a leftover on a closed
  coin only when it is worth less than the 5 USDT minimum order (unsellable
  dust); a sellable leftover is still flagged.
