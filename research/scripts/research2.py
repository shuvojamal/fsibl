"""Research round 2, three questions about the opportunity scorer:
  A. Does a BTC regime filter (only enter when BTC is above its 200-day EMA) help?
  B. Is the universal daily setting stable across different train/test windows?
  C. Does the scorer work on 4h candles with the 3:1 target and a stricter score?
"""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')      # cached candles
RES = _os.path.join(HERE, '..', 'results')   # tables written here
import itertools, os, pickle, sys, time
sys.path.insert(0, ROOT)
from tradebot import backtest
from tradebot.data import fetch_candles
from tradebot.indicators import ema
from tradebot.opportunity import Opportunity, OppParams

SYMS = "BTCUSDT ETHUSDT SOLUSDT XRPUSDT DOGEUSDT ADAUSDT LINKUSDT AVAXUSDT DOTUSDT LTCUSDT".split()
daily = pickle.load(open(f'{OUT}/daily10.pkl', 'rb'))
cache4 = f'{OUT}/h4_10.pkl'
if os.path.exists(cache4):
    h4 = pickle.load(open(cache4, 'rb'))
else:
    h4 = {}
    for s in SYMS:
        h4[s] = fetch_candles(s, '4h', 5000); time.sleep(0.3)
    pickle.dump(h4, open(cache4, 'wb'))

UNI = dict(min_score=5, stop_atr=2.0, reward_risk=3.0)
lines = []


class RegimeFiltered(Opportunity):
    """Opportunity scorer that also requires BTC to be above its 200-day EMA
    at the same candle (market-wide risk-on filter)."""
    def __init__(self, p, btc_ok):
        super().__init__(p)
        self.btc_ok = btc_ok  # dict open_time -> bool
        self.times = []
    def prepare(self, candles):
        self.times = [c.open_time for c in candles]
        return super().prepare(candles)
    def signal(self, i):
        if not self.btc_ok.get(self.times[i], False):
            return None
        return super().signal(i)


def btc_regime(btc_candles):
    c = [x.close for x in btc_candles]
    e = ema(c, 200)
    return {x.open_time: (e[i] is not None and c[i] > e[i]) for i, x in enumerate(btc_candles)}


def table(title, rows):
    lines.append(f"\n### {title}\n")
    lines.append(f"{'coin':9} | {'plain test':>10} | {'filtered test':>13} | {'trades':>8} | {'win':>9} | {'PF':>11} | {'B&H':>7}")
    for r in rows:
        lines.append(r)


# ---- A. regime filter, same 70/30 split as round 1
btc_ok = btc_regime(daily['BTCUSDT'])
plain_sum = filt_sum = 0; plain_pos = filt_pos = 0
rows = []
for s, cs in daily.items():
    split = int(len(cs) * 0.7)
    test = cs[split:]
    rp = backtest.run_opportunity(test, Opportunity(OppParams(**UNI)))
    rf = backtest.run_opportunity(test, RegimeFiltered(OppParams(**UNI), btc_ok))
    plain_sum += rp.total_return; filt_sum += rf.total_return
    plain_pos += rp.total_return > 0; filt_pos += rf.total_return > 0
    rows.append(f"{s:9} | {rp.total_return:+10.1%} | {rf.total_return:+13.1%} | {len(rp.trades):3}/{len(rf.trades):<3} | "
                f"{rp.win_rate:4.0%}/{rf.win_rate:<4.0%} | {rp.profit_factor:5.2f}/{rf.profit_factor:<5.2f} | {rp.buy_hold_return:+7.1%}")
table("A. BTC regime filter (plain / BTC>EMA200 filtered), daily, test 2025-07-29 -> 2026-10-21", rows)
lines.append(f"AVERAGE   | {plain_sum/10:+10.1%} | {filt_sum/10:+13.1%} | profitable coins {plain_pos}/10 vs {filt_pos}/10")

# ---- B. window stability: splits at 50/60/70/80%, universal re-chosen on each train part
grid = {'min_score': [4, 5, 6], 'stop_atr': [1.5, 2.0, 3.0], 'reward_risk': [1.5, 2.0, 3.0]}
combos = [dict(zip(grid, v)) for v in itertools.product(*grid.values())]
lines.append("\n### B. Window stability (daily, universal setting re-chosen per split)\n")
lines.append(f"{'split':>5} | {'test window':>23} | {'chosen universal setting':>44} | {'avg test':>8} | {'profitable':>10} | {'avg B&H':>8}")
from datetime import datetime, timezone
d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m-%d')
for frac in (0.5, 0.6, 0.7, 0.8):
    scores = {str(p): 0.0 for p in combos}
    for s, cs in daily.items():
        split = int(len(cs) * frac)
        for p in combos:
            r = backtest.run_opportunity(cs[:split], Opportunity(OppParams(**p)))
            scores[str(p)] += (r.total_return if len(r.trades) >= 8 else -9)
    uni = max(combos, key=lambda p: scores[str(p)])
    rets, bhs = [], []
    for s, cs in daily.items():
        split = int(len(cs) * frac)
        r = backtest.run_opportunity(cs[split:], Opportunity(OppParams(**uni)))
        rets.append(r.total_return); bhs.append(r.buy_hold_return)
    cs = daily['BTCUSDT']; split = int(len(cs) * frac)
    lines.append(f"{frac:5.0%} | {d(cs[split].open_time)} -> {d(cs[-1].close_time)} | {str(uni):>44} | "
                 f"{sum(rets)/10:+8.1%} | {sum(x > 0 for x in rets):>7}/10 | {sum(bhs)/10:+8.1%}")

# ---- C. 4h candles, 3:1 target, stricter score; 70/30 split
lines.append("\n### C. 4h candles, reward_risk 3.0, 70/30 split\n")
lines.append(f"{'min_score':>9} | {'stop_atr':>8} | {'avg train':>9} | {'avg test':>8} | {'profitable':>10} | {'trades/coin':>11} | {'avg B&H test':>12}")
for ms in (5, 6, 7):
    for sa in (2.0, 3.0):
        p = OppParams(min_score=ms, stop_atr=sa, reward_risk=3.0)
        tr, te, bh, n, pos = 0, 0, 0, 0, 0
        for s, cs in h4.items():
            split = int(len(cs) * 0.7)
            a = backtest.run_opportunity(cs[:split], Opportunity(p))
            b = backtest.run_opportunity(cs[split:], Opportunity(p))
            tr += a.total_return; te += b.total_return; bh += b.buy_hold_return
            n += len(b.trades); pos += b.total_return > 0
        lines.append(f"{ms:>9} | {sa:>8} | {tr/10:+9.1%} | {te/10:+8.1%} | {pos:>7}/10 | {n/10:>11.1f} | {bh/10:+12.1%}")
cs = h4['BTCUSDT']; split = int(len(cs) * 0.7)
lines.append(f"(4h data {d(cs[0].open_time)} -> {d(cs[-1].close_time)}, test from {d(cs[split].open_time)})")

open(f'{RES}/research2.md', 'w').write("\n".join(lines) + "\n")
print("\n".join(lines))
