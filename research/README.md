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
