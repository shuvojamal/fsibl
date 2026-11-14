# Research archive

Everything behind the strategy decisions: the scripts that were run, their
raw output, the cached price data they ran on, and the logs of the live
experiments. The written conclusions for each round are in `../docs/`.

```
research/
  scripts/   the exact scripts, one per round (paths made repo-relative)
  results/   raw console output of each run (researchN.out), plus logs
  data/      cached Binance candles the scripts read (pickle, regenerable)
```

## Rounds

| Round | Script | Output | Write-up | Ran on code at | Question |
|---|---|---|---|---|---|
| 0a | `opp_eval.py` | (in chat) | `docs/opportunity-backtest-2026-10-22.md` | `b5c68a8` | Opportunity scorer on 1h candles, thresholds 4–7 |
| 0b | `opp_tf.py` | `opp_tf.out` | same | `b5c68a8` | Same on 4h and daily candles, walk-forward |
| 1 | `research1.py` | `research1.out` | `docs/research-round1-…` | `b5c68a8` | Scorer vs Donchian breakout vs RSI(2) dip-buying, per-coin vs universal tuning |
| 2 | `research2.py` | `research2.out` | `docs/research-round2-…` | `4a7e4a0` | BTC regime filter, window stability, 4h |
| 3 | `research3.py` | `research3.out` | `docs/research-round3-…` | `b801c95` (+ trailing-stop hook) | Trailing stops, volatility-scaled risk |
| 4 | `research4.py` | `research4.out` | `docs/research-round4-…` | `b3881b6` | One shared account, cap on open positions |
| 5 | `research5.py` | `research5.out` | `docs/research-round5-…` | `d15a4fb` (+ warm-up fix) | Window tests redone with warmed-up indicators |
| 6 | `research6.py` | `research6.out` | `docs/research-round6-…` | `870bc62` | Pyramiding, drawdown throttle, second coin universe |
| 7 | `research7.py`, `research7b.py` | `research7.out`, `research7b.out` | `docs/research-round7-…` | `591f4f1` | Ablation of the 8 checks, threshold, costs; RSI-zone verification |
| 8 | `research8.py` | `research8.out` | `docs/research-round8-…` | `fc95fc3` | Time exits, re-entry cooldown, third coin universe |
| 9 | `research9.py` | `research9.out` | `docs/research-round9-…` | `e744b5a` | Volume-ranked universe rule (no hindsight) |
| 10 | `research10.py` | `research10.out` | `docs/research-round10-…` | `02d7b0b` | Partial profit-taking |
| 11 | `research11.py` | `research11.out` | `docs/research-round11-…` | `c2f1495` | Which signal gets a free slot; cost of checking stops once a day |
| 12 | `research12.py`, `research12b.py` | `research12.out`, `research12b.out` | `docs/research-round12-…` | `196a899` | 9-year stress test (2017–2026), Sharpe/expectancy/regimes, Monte Carlo; ADX filter and top-10 checked on each half |
| 13 | `research13.py` | `research13.out`, `research13-funding-now.out` | `docs/research-round13-2026-10-23.md` | `9373e95` | Funding-rate carry (spot long + perp short), 20 coins 2020–2026, tuned 2020–23, tested 2024–26; added `tradebot funding` monitor |
| 14 | `research14.py` | `research14.out` | `docs/research-round14-2026-10-23.md` | `ae2293c` | Cross-sectional momentum rotation (64 settings, BTC filter), vs and blended with the trend bot |
| 15 | `research15.py` | `research15.out` | `docs/research-round15-2026-10-23.md` | `bdf2b96` | Kronos-small forecasts on 15 coins, 2025-09 to 2026-10 (after the model's release): IC, hit rate, top-3 portfolio |
| R1 | `review_jev.py` | `review_jev.out` | `docs/review-jev-trades-2026-10-23.md` | `2f76d15` | Review of github.com/zadescoxp/Jev-Trades: its own saved paper trades, re-priced with fees |
| R2 | (reading only) | — | `docs/review-autotrader-2026-10-23.md` | `4a079f5` | Review of github.com/PkLavc/Autotrader (Kronos model on US stocks); led to round 15 |
| 16 | `research16.py` | `research16.out` | `docs/research-round16-2026-10-23.md` | `3194d01` | Deflated Sharpe ratio of the live rules vs the number of variants tried |
| 17 | `research17.py` | `research17.out` | `docs/research-round17-2026-10-23.md` | `3d193ea` | Gold via PAXG: rules alone, correlation, as a 16th symbol in the book, gold sleeve |
| 18 | `research18.py` | `research18.out` | `docs/research-round18-2026-10-23.md` | `1102fa9` | Live rules on XM-style CFD markets (gold, silver, oil, 4 indices, 4 FX pairs) with overnight swap costs |
| 19 | `research19.py` | `research19.out` | `docs/research-round19-2026-10-23.md` | `0a12bf6` | Execution: exchange stop orders vs daily-close stops, backstops, limit entries |
| 20 | `research20.py` | `research20.out` | `docs/research-round20-2026-10-23.md` | `f87647f` | Short side: mirrored rules on inverted prices with real funding, alone and sharing slots with the longs |
| 21 | `research21.py` | `research21.out` | `docs/research-round21-2026-10-23.md` | `34ce28a` | Robustness: the same rules on daily candles closing at 00/04/08/12/16/20 UTC (rebuilt from hourly data) |
| 22 | `research22.py` | `research22.out` | `docs/research-round22-2026-10-23.md` | `1730dcc` | Tranching: equal sub-books on different daily close times vs the single 00:00 close |
| 23 | `research23.py` | `research23.out` | `docs/research-round23-2026-10-23.md` | `659060b` | Cost of entering 0-20 h after the close, and the 2% price guard (failed as an anti-chase rule; now compares against Binance's live price) |
| 24 | `research24.py` | `research24.out` | `docs/research-round24-2026-10-24.md` | `b3b6d74` | min_score 4/5/6/7 on 6 close times x 2 halves: 6 wins Sharpe in 11 of 12 cells but loses the live cell; fails the pre-set bar; made a setting |
| 25 | `research25.py` | `research25.out` | `docs/research-round25-2026-10-24.md` | `0dba740` | Financial model: 300 USDT (and +50/month) over 1-5 years, 4,000 block-bootstrap paths from six close-time backtests; backtest / realistic / half-size vs holding BTC and savings |
| 26 | `research26.py` | `research26.out` | `docs/research-round26-2026-10-24.md` | `95ccd22` | Hold vs trade, coin by coin (55 coins): holding made money on 20, median -37%, median worst drop -96%; trend rule made money on 48, smaller drop on all 55 |
| 27 | `research27.py` | `research27.out` | `docs/research-round27-2026-10-24.md` | `061e450` | Trailing-stop distance: ATR x2-5 and 10-25% trails on 6 close times x 2 halves; trail good, best width market-dependent; 25% "beats" 3xATR 11/12 but ties in 2022-26; no change |
| 28 | `research28.py` | `research28.out` | `docs/research-round28-2026-10-24.md` | `066476b` | Max positions 3/5/8/10 x risk 0.5/1/1.5% on 12 cells: 8 slots at 0.5% beats live 12/12 (2022-26 +13.5% vs +10.8%, DD -21.7% vs -30.4%); recommended to the owner |
| 29 | `research29.py` | `research29.out` | `docs/research-round29-2026-10-24.md` | `0a8b18b` | With 8 x 0.5%: universe top 10/15/20/25 x 5/6 checks; 6 checks now passes (top 15: 2022-26 +15.7% vs +13.5%, DD -16% vs -22%); wider lists pass but are hindsight-prone |
| 30 | `research30.py` | `research30.out` | `docs/research-round30-2026-10-24.md` | `ebc2232` | Regime-based risk (more risk while BTC > 200-EMA): fails; found 8 slots x 1% with 6 checks = 2022-26 +25.9%, DD -28% (growth setting) |
| 31 | `research31.py` | `research31.out` | `docs/research-round31-2026-10-24.md` | `aa3f404` | Pyramiding: 1-2 adds at +1R/+2R on steady and growth set-ups; fails (Sharpe flat or lower, drops deeper); no change |
| 32 | `research32.py` | `research32.out` | `docs/research-round32-2026-10-24.md` | `f7eccdc` | Interest on idle USDT (flexible savings at 2/4/6%): cash is 63-80% of the account; 4% adds +3.1 to +3.7 pts/yr with shallower drops; passes; auto-savings not built yet |
| 33 | `research33.py` | `research33.out` | `docs/research-round33-2026-10-24.md` | `630699f` | The 8 buy checks: payoff by score (rises 4->7), each check's value, remove/require each (16 variants, 12 cells): only 'trend_up removed' passes (10/12), confirmed on the 55-coin pool; made an app switch, default unchanged |
| 34 | `research34.py` | `research34.out` | `docs/research-round34-2026-10-24.md` | `127a429` | Initial stop 1.5/2/2.5/3/4 x ATR (12 cells, steady set-up): Sharpe flat (0.97-1.03), tighter stop = bigger positions; 1.5x 9/12 but DD 4 pts deeper, fails; no change |
| 35 | `research35.py` | `research35.out` | `docs/research-round35-2026-10-25.md` | `1b1d600` | Risk profile steady vs growth (12 cells): worst 30 days -14% vs -24%, worst year -10% vs -20%, both ~21 months below the high in 2022-23, 57% losing months; neither passes the pre-set bar (duration); steady recommended for first real money |
| 36 | `research36.py` | `research36.out` | `docs/research-round36-2026-10-25.md` | `dd58c69` | 500 USDT x 5 years, current set-ups, bootstrap: realistic median CAGR steady 10% (13% with savings) on 2022-26 markets, 17-20% on all history; growth 16-17% / 30-33%; owner's question |
| 37 | `research37.py` | `research37.out` | `docs/research-round37-2026-10-25.md` | `2005c50` | Chance of 30%/yr over 5 years by risk 0.5/1/1.5/2%: 17/57/61/65% on all history, 6/24/16/18% on 2022-26; above 1% the 2022-26 median falls and loss odds double; never above 1% |
| 38 | `research38.py` | `research38.out` | `docs/research-round38-2026-10-25.md` | `b684a8e` | Live rules on DSE shares (393 equities, adjusted, 2012-26, Mendeley CC BY 4.0, cached `dse_daily_adj.pkl.gz`): loses money in both halves (-16%/-13% a year) vs DSEX +3%; costs vs tight stops, gross edge ~0; rejected |
| 39 | `research39.py` | `research39.out` | `docs/research-round39-2026-10-25.md` | `1d0427f` | 1999-2025 DSE dataset (Mendeley 5mww8rb9td, unadjusted): self-detection of bonuses finds 29 of 1,236 events (markers only from 2023); unusable for extending round 38; not cached |
| 40 | `research40.py` | `research40.out` | `docs/research-round40-2026-10-25.md` | `2acc537` | Quarterly DSE portfolios (momentum, low-vol, combo, filter; top-50 liquid, 0.7%/side): all lose or trail DSEX (+2%/yr) in both halves; only 2% of shares made 30%+/yr over 5/10 years, median share ~-5%/0%; fails |
| 41 | `research41.py` | `research41.out` | `docs/research-round41-2026-10-25.md` | `99ca9d7` | Owner's six DSE shares (BRAC, Uttara, Kohinoor, Square, Marico, Ibn Sina): 10y price+bonus CAGR 2-16%, basket +15%/+12% a year (hindsight) vs DSEX +2%; a price-only quality screen picking in advance: -6%/-1%, fails |
| 42 | `research42.py` | `research42.out` | `docs/research-round42-2026-10-25.md` | `a886c22` | CFA post's 30 DSE blue chips in our data 2013-26: median share +3.5%/yr price+bonus, equal-weight basket +8.6%/yr vs DSEX +2.2% (about 13-15% with dividends); gap to the post = dividends, 2001 start, hindsight list |
| 43 | `research43.py` | `research43.out` | `docs/research-round43-2026-10-26.md` | `34c3ad7` | Per-position size cap 50/33/20% of equity (steady and growth, 12 cells): caps almost never bind (positions ~5-17% of equity); no pass, no change |
| 44 | `research44.py` | `research44.out` | `docs/research-round44-2026-10-27.md` | `23c3739` | 'Skip the 200-day trend check' on the growth set-up: 9/12 cells (6/6 bull, 3/6 recent), drop and 55-coin tests pass; fails the 10/12 bar narrowly; not for the growth account |
| 45 | `research45.py` | `research45.out` | `docs/research-round45-2026-10-28.md` | `c191a04` | Position size distribution (after a 50% TRX buy on the VPS): growth median 9%, max 47%, >25% only TRX (1.6% of trades), worst big-position loss -1.4% of equity; no cap; corrects round 43's '5-17%' as the typical range; notes Binance accounts lack a backstop |
| 46 | `research46.py` | `research46.out` | `docs/research-round46-2026-10-29.md` | `3240bd6` | Missed days (no run): 5% random, 3 or 7 days a month, 30 days a year; all tolerable (worst: 7 days/month -3 pts/yr in 2022-26); crash-during-outage risk is what a backstop is for |
| 47 | `research47.py` | `research47.out` | `docs/research-round47-2026-10-30.md` | `ecbb40c` | Minimum initial stop distance 3%/5% (calm coins like TRX): practically no effect on growth or steady; no pass, no change |
| 48 | `research48.py` | `research48.out` | `docs/research-round48-2026-10-31.md` | `635d019` | Losing streaks (after the testnet's first 3 trades all lost): win rate 41%, 3+ streaks ~3.7/yr, first 3 trades all lose ~48% of starts (losses cluster); normal, no action |
| 49 | `research49.py` | `research49.out` | `docs/research-round49-2026-11-01.md` | `0d8f784` | Coin collapses 90% while held: account loss growth 8%/14%/42% (median/90th/worst) without a backstop vs 3%/5%/14% with one; passes; Binance backstop recommended before real money |
| 50 | `research50.py` | `research50.out` | `docs/research-round50-2026-11-02.md` | `f6c7e53` | Deflated Sharpe updated for ~600 variants tried and the current set-ups: steady DSR 0.988 (0.89 harsh), growth 0.990 (0.91); passes; edge still clears the luck bar |
| 51 | `research51.py` | `research51.out` | `docs/research-round51-2026-11-03.md` | `ee4ec33` | 90-day windows: ~half lose (60% in 2022-26), median ~0, 90th pct +20%/+40%; the 90-day demo tests execution, not profitability; red flags below -7% (steady) / -13% (growth) |
| 52 | `research52.py` | `research52.out` | `docs/research-round52-2026-11-04.md` | `132c36b` | 300-500 USDT account vs Binance's 5 USDT minimum: steady 0% buys skipped, same returns (fine); growth 13% skipped (mostly no-cash leftovers), -0.3 pts/yr |
| 53 | `research53.py` | `research53.out` | `docs/research-round53-2026-11-05.md` | `0453031` | Max new buys per day 1/2/3: max 3 rarely binds (ties 'win' 9-10/12 by noise), max 1 trims drops 1-3 pts but costs 1.4-3 pts/yr; no change; pass bar needs an effect-size floor |
| 54 | `research54.py` | `research54.out` | `docs/research-round54-2026-11-06.md` | `02e1892` | Second-day confirmation before buying: win rate 36->39%, trades -30%, bull-market returns halved (steady 2018-21 +29.5% -> +12.7%); fails; no change |
| 55 | `research55.py` | `research55.out` | `docs/research-round55-2026-11-07.md` | `e17edb2` | Indicator lengths moved ~25% (10 variants): fast EMA 15/25 and ATR 10/20 give ~12-13% vs 15.7% in 2022-26 (equal in 2018-21); fails robustness bar; live set-up is on a recent-years peak; plan ~12%/yr for steady; no change |
| 56 | `research56.py` | `research56.out` | `docs/research-round56-2026-11-08.md` | `9c262fc` | Nine-setting ensemble (fast EMA x ATR neighbours): 2022-26 +14.0% vs live +15.7%, slightly better worst cell and 2018-21; fails narrowly; fairer estimate of the rule family; no change |
| 57 | `research57.py` | `research57.out` | `docs/research-round57-2026-11-09.md` | `36d37d5` | Fees 0.075/0.10/0.15% x slippage 0.02/0.05/0.15%: BNB fees +0.2 pts (steady) / +0.4 (growth); each +0.05%/side -0.4/-0.8 pts; costs a small factor |
| 58 | `research58.py` | `research58.out` | `docs/research-round58-2026-11-10.md` | `311f3d9` | Tighter trail after +3R/+5R (2 or 2.5 x ATR): avg trade +0.65R -> +0.45R, 2022-26 return -1 to -7 pts; fails; keep 3 x ATR for the whole trade |
| 59 | `research59.py` | `research59.out` | `docs/research-round59-2026-11-11.md` | `527fdb7` | Overshoot past daily-close stops: median loser -0.85R, 5.7% worse than -1.5R, 1.8% worse than -2R; fails the 5% bar narrowly; known cost of close stops (round 19); no change |
| 60 | `research60.py` | `research60.out` | `docs/research-round60-2026-11-12.md` | `6784213` | Testnet first 20 days -6.0% (growth): 8th percentile of 2022-26 20-day windows (5th pct -7.0%); consistent with the backtest, an unlucky start; execution matches |
| 61 | `research61.py` | `research61.out` | `docs/research-round61-2026-11-13.md` | `2177993` | Cool-off after K losses (K=3/5, 7/14 days): after-3 pauses cost 4-6 pts/yr (miss the next trend's start), after-5 neutral; fails; no pause |
| 62 | `research62.py` | `research62.out` | `docs/research-round62-2026-11-14.md` | `4fe6180` | Meme coins (DOGE/SHIB/PEPE) out: 2022-26 steady +15.7->+17.6%, growth +25.9->+27.4%, 10/12 cells each, confirmed on the 55-coin pool; passes; recommend an optional switch |
| R3 | (reading only) | — | `docs/review-batch-2026-10-23.md` | `3194d01` | martex-quant (honest crypto ledger), Forex HEX (ad), Krexibd/quant-trading (MALWARE), ai4trade skill |

Earlier experiments:
- **Cross-exchange arbitrage** (9 exchanges, 10 coins): `results/arbitrage/`,
  write-up `docs/arb-scan-2026-10-22.md`.
- **Paper trading on live prices** (EMA and opportunity, 1h, 10 coins,
  14:25–16:25 UTC, no trades): `results/paper_demo/`.
- **OKX demo**: test order and bot runs are recorded in the conversation
  and in `docs/`; the bot's own state lived in its session and is gone.

## Re-running

```bash
python research/scripts/research9.py        # from the repo root
```

The scripts import the current `tradebot` package, so re-running one today
uses today's defaults (for example, the RSI zone became 40–80 in round 7).
To reproduce a round's numbers exactly, check out the commit in the "Ran on
code at" column first:

```bash
git checkout 4a7e4a0 -- tradebot && python research/scripts/research2.py && git checkout HEAD -- tradebot
```

Rounds 7b, 8 and 10 reuse helper code from `research7.py` / `research9.py`
in the same folder. Missing data caches are fetched from Binance's public
API and saved to `data/` on first use. The `.pkl` files are pickled
`tradebot.data.Candle` lists; only load caches you made yourself.
