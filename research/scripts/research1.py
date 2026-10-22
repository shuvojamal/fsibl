"""Strategy research round 1: three strategy families, 10 coins, daily candles,
walk-forward (tune on first 70%, judge on last 30%). Also a 'universal' pick:
the one parameter set that does best across ALL coins on the training data,
then judged per coin on test data, which is the honest way to avoid tuning
each coin to its own past."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')      # cached candles
RES = _os.path.join(HERE, '..', 'results')   # tables written here
import itertools, os, pickle, sys, time
sys.path.insert(0, ROOT)
from tradebot import backtest
from tradebot.data import fetch_candles
from tradebot.indicators import atr, ema, rolling_max, rsi
from tradebot.opportunity import Opportunity, OppParams, Plan

SYMS = "BTCUSDT ETHUSDT SOLUSDT XRPUSDT DOGEUSDT ADAUSDT LINKUSDT AVAXUSDT DOTUSDT LTCUSDT".split()
cache = f'{OUT}/daily10.pkl'
if os.path.exists(cache):
    data = pickle.load(open(cache, 'rb'))
else:
    data = {}
    for s in SYMS:
        data[s] = fetch_candles(s, '1d', 1500); time.sleep(0.3)
    pickle.dump(data, open(cache, 'wb'))


def rolling_min(values, period):
    out = [None] * len(values)
    for i in range(period - 1, len(values)):
        out[i] = min(values[i - period + 1:i + 1])
    return out


class Donchian:
    """Classic breakout: buy a close above the N-day high, exit on a close below
    the M-day low or an ATR stop. The 'turtle' rule."""
    def __init__(self, entry=55, exit_=20, stop_atr=2.0, risk=0.01):
        self.entry, self.exit_, self.stop_atr, self.risk = entry, exit_, stop_atr, risk
    def prepare(self, cs):
        self.c = [x.close for x in cs]
        self.hi = rolling_max([x.high for x in cs], self.entry)
        self.lo = rolling_min([x.low for x in cs], self.exit_)
        self.a = atr([x.high for x in cs], [x.low for x in cs], self.c)
        self.t = ema(self.c, 200)
        return self
    def signal(self, i):
        if i < 1 or None in (self.hi[i - 1], self.a[i], self.t[i]):
            return None
        if self.c[i] > self.hi[i - 1] and self.c[i] > self.t[i]:
            stop = self.c[i] - self.stop_atr * self.a[i]
            return Plan(stop, self.c[i] * 100, 0, ['breakout'])  # no target: ride the trend
        return None
    def should_exit(self, i):
        return self.lo[i - 1] is not None and self.c[i] < self.lo[i - 1]
    def size(self, equity, price, stop):
        r = price - stop
        return min(equity * self.risk / r, equity / price) if r > 0 else 0.0


class MeanRev:
    """RSI(2) dip-buy in an uptrend (Connors): buy when RSI2 < lo and close > EMA200,
    exit when close > EMA5 or RSI2 > hi. ATR stop."""
    def __init__(self, lo=10, hi=70, stop_atr=2.0, risk=0.01):
        self.lo, self.hi, self.stop_atr, self.risk = lo, hi, stop_atr, risk
    def prepare(self, cs):
        self.c = [x.close for x in cs]
        self.r = rsi(self.c, 2); self.t = ema(self.c, 200); self.e5 = ema(self.c, 5)
        self.a = atr([x.high for x in cs], [x.low for x in cs], self.c)
        return self
    def signal(self, i):
        if None in (self.r[i], self.t[i], self.a[i]):
            return None
        if self.r[i] < self.lo and self.c[i] > self.t[i]:
            return Plan(self.c[i] - self.stop_atr * self.a[i], self.c[i] * 100, 0, ['rsi2_dip'])
        return None
    def should_exit(self, i):
        return self.e5[i] is not None and (self.c[i] > self.e5[i] or self.r[i] > self.hi)
    def size(self, equity, price, stop):
        r = price - stop
        return min(equity * self.risk / r, equity / price) if r > 0 else 0.0


FAMILIES = {
    'opportunity': (lambda **k: Opportunity(OppParams(**k)),
                    {'min_score': [4, 5, 6], 'stop_atr': [1.5, 2.0, 3.0], 'reward_risk': [1.5, 2.0, 3.0]}),
    'donchian': (lambda **k: Donchian(**k),
                 {'entry': [20, 55, 100], 'exit_': [10, 20], 'stop_atr': [2.0, 3.0]}),
    'meanrev': (lambda **k: MeanRev(**k),
                {'lo': [5, 10, 15], 'hi': [60, 70, 80], 'stop_atr': [1.5, 2.0, 3.0]}),
}


def run(fam, params, cs):
    make = FAMILIES[fam][0]
    return backtest.run_opportunity(cs, make(**params))


def score(r, min_trades=8):
    """Rank by return but demand enough trades to mean something."""
    return r.total_return if len(r.trades) >= min_trades else -9


results = {}
lines = []
for fam, (make, grid) in FAMILIES.items():
    combos = [dict(zip(grid, v)) for v in itertools.product(*grid.values())]
    lines.append(f"\n##### {fam}: {len(combos)} parameter sets\n")
    train_scores = {str(p): [] for p in combos}
    per_coin_best = {}
    for s, cs in data.items():
        split = int(len(cs) * 0.7)
        best = None
        for p in combos:
            r = run(fam, p, cs[:split])
            train_scores[str(p)].append(score(r))
            if best is None or score(r) > score(best[1]):
                best = (p, r)
        per_coin_best[s] = best
    # universal: the parameter set with the best MEAN training score across coins
    uni = max(combos, key=lambda p: sum(train_scores[str(p)]) / len(SYMS))
    lines.append(f"universal params (best average on training data): {uni}\n")
    lines.append(f"{'coin':9} | {'per-coin tuned: train':>22} | {'test':>8} | {'universal: train':>17} | {'test':>8} | {'trades':>6} | {'win':>5} | {'PF':>5} | {'B&H test':>9} | {'maxDD':>7}")
    agg = {'tuned_test': [], 'uni_test': [], 'bh': [], 'uni_pf': []}
    for s, cs in data.items():
        split = int(len(cs) * 0.7)
        p, rtr = per_coin_best[s]
        rte = run(fam, p, cs[split:])
        utr = run(fam, uni, cs[:split]); ute = run(fam, uni, cs[split:])
        agg['tuned_test'].append(rte.total_return); agg['uni_test'].append(ute.total_return)
        agg['bh'].append(ute.buy_hold_return); agg['uni_pf'].append(ute.profit_factor)
        lines.append(f"{s:9} | {rtr.total_return:+21.1%} | {rte.total_return:+7.1%} | {utr.total_return:+16.1%} | "
                     f"{ute.total_return:+7.1%} | {len(ute.trades):6} | {ute.win_rate:5.0%} | {ute.profit_factor:5.2f} | "
                     f"{ute.buy_hold_return:+8.1%} | {ute.max_drawdown:6.1%}")
    n = len(SYMS)
    lines.append(f"{'AVERAGE':9} | {'':>22} | {sum(agg['tuned_test'])/n:+7.1%} | {'':>17} | {sum(agg['uni_test'])/n:+7.1%} | "
                 f"{'':6} | {'':5} | {'':5} | {sum(agg['bh'])/n:+8.1%} |")
    lines.append(f"coins profitable on test (universal): {sum(x > 0 for x in agg['uni_test'])}/{n}; "
                 f"beat buy&hold: {sum(a > b for a, b in zip(agg['uni_test'], agg['bh']))}/{n}")
    results[fam] = {'uni': uni, 'uni_test': agg['uni_test'], 'tuned_test': agg['tuned_test'], 'bh': agg['bh']}

from datetime import datetime, timezone
d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m-%d')
cs = data['BTCUSDT']; split = int(len(cs) * 0.7)
header = (f"Daily candles, 10 coins. Train {d(cs[0].open_time)} -> {d(cs[split].open_time)}, "
          f"test {d(cs[split].open_time)} -> {d(cs[-1].close_time)}. Fees 0.1%/side, slippage 0.05%, "
          f"1% equity risked per trade, next-open fills.")
open(f'{RES}/research1.md', 'w').write(header + "\n" + "\n".join(lines) + "\n")
pickle.dump(results, open(f'{RES}/research1.pkl', 'wb'))
print(header); print("\n".join(lines))
