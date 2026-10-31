# Research round 48: how normal are losing streaks? (scheduled daily run)

**Prompt.** The VPS testnet's first three closed trades were all losers
(BNB −52.45, BTC −51.06, TRX −53.08 USDT on 2026-10-30/31; −3.1% of 5,000).
TRX had been +210 USDT the day before and fell through its raised stop
overnight; stops act at the daily close, so it sold at 0.3248 against a
0.3352 stop.

**Method.** Trade sequences from round 12's simulator, steady and growth,
6 of 8 checks, top 15, round 21's six close times, 2018-03 .. 2026-10.
Pass bar (expectation test, set first): three straight losers is "normal, no
action" if 3+ streaks happen at least 3 times a year on median and a new
account's first three trades all lose in at least 15% of start days.

**Result** (`research/results/research48.out`, both set-ups similar):
- Win rate 41%.
- Streaks of 3+ losers: about 3.7 a year; 5+: 2 a year; 8+: about once a year.
- Longest streak in a run: median 16-18, worst 19.
- A new account's first 3 trades are all losers about **48%** of the time
  (38-55%), far more than independent coin flips would give (about 20%),
  because losses cluster: when the market turns, several positions stop out
  together.
- The worst streak's total loss, measured against typical equity: steady
  about −14% (worst −22%); growth about −31% (worst −46%). Rough measure.

**Verdict: normal, no action.** The testnet's start is what the backtest
expects about half the time. Judging the bot needs dozens of trades, not
three (with fewer than 30, results are mostly luck).
