"""Research round 7, 20-coin shared account (max 5 open, 1% risk, trailing scorer):
  A. Ablation: force each of the 8 checks to 'pass' (i.e. stop requiring it).
  B. Threshold: 4 / 5 / 6 of 8.
  C. Costs: normal (0.1% fee, 0.05% slip), double, triple."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')      # cached candles
RES = _os.path.join(HERE, '..', 'results')   # tables written here
import pickle, sys
sys.path.insert(0, ROOT)
from tradebot.opportunity import Opportunity, OppParams
from datetime import datetime, timezone

d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m-%d')
data = {**pickle.load(open(f'{OUT}/daily10.pkl', 'rb')), **pickle.load(open(f'{OUT}/daily_new10.pkl', 'rb'))}
CHECKS = ["trend_up", "ema_aligned", "momentum", "rsi_zone", "volume", "volatility_ok", "breakout", "pullback"]


class Ablated(Opportunity):
    def __init__(self, p, skip):
        super().__init__(p); self.skip = skip
    def checks(self, i):
        cs = super().checks(i)
        return None if cs is None else [(n, True if n == self.skip else ok) for n, ok in cs]


def portfolio(make, fee=0.001, slip=0.0005, max_open=5, risk=0.01, capital=10000.0, start_frac=0.0):
    strats = {s: make().prepare(cs) for s, cs in data.items()}
    idx = {s: {c.open_time: i for i, c in enumerate(cs)} for s, cs in data.items()}
    times = sorted(set(t for s in data for t in idx[s]))
    start_t = times[int(len(times) * start_frac)]
    cash, pos, pending, trades, curve = capital, {}, {}, [], []
    eq_of = lambda t: cash + sum(q['qty'] * data[k][idx[k][t]].close for k, q in pos.items() if t in idx[k])
    for t in times:
        if t < start_t:
            continue
        eq_now = curve[-1] if curve else capital
        for s, (action, plan) in list(pending.items()):
            i = idx[s].get(t)
            if i is None:
                continue
            c = data[s][i]
            if action == 'buy' and s not in pos and len(pos) < max_open:
                entry = c.open * (1 + slip)
                qty = min(eq_now * risk / (entry - plan.stop), cash * (1 - fee) / entry)
                if qty > 0:
                    cash -= qty * entry / (1 - fee)
                    pos[s] = dict(qty=qty, cost=qty * entry, stop=plan.stop, peak=entry)
            elif action == 'sell' and s in pos:
                px = c.open * (1 - slip); cash += pos[s]['qty'] * px * (1 - fee)
                trades.append((pos[s]['cost'], pos[s]['qty'] * px)); del pos[s]
        pending = {}
        for s, cs in data.items():
            i = idx[s].get(t)
            if i is None:
                continue
            c, st = cs[i], strats[s]
            if s in pos:
                q = pos[s]
                if c.low <= q['stop']:
                    px = min(q['stop'], c.open) * (1 - slip); cash += q['qty'] * px * (1 - fee)
                    trades.append((q['cost'], q['qty'] * px)); del pos[s]; continue
                st.peak = max(q['peak'], c.close); q['peak'] = st.peak
                q['stop'] = st.update_stop(i, q['stop'])
                if st.should_exit(i):
                    pending[s] = ('sell', None)
            else:
                plan = st.signal(i)
                if plan:
                    pending[s] = ('buy', plan)
        curve.append(eq_of(t))
    for s, q in pos.items():
        trades.append((q['cost'], q['qty'] * data[s][-1].close * (1 - slip)))
    final = curve[-1]; pk = dd = 0
    for e in curve:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    wins = [(a, b) for a, b in trades if b * (1 - fee) > a]
    g = sum(b * (1 - fee) - a for a, b in wins); l = -sum(b * (1 - fee) - a for a, b in trades if (a, b) not in wins)
    return dict(ret=final / capital - 1, dd=dd, n=len(trades), win=len(wins) / max(1, len(trades)), pf=g / l if l else 99)


WINDOWS = [(0.0, 'full 4y'), (0.5, 'from 2024-10'), (0.7, 'from 2025-07'), (0.8, 'from 2025-12')]
def line(label, make, **kw):
    cells = []
    for w, _ in WINDOWS:
        r = portfolio(make, start_frac=w, **kw)
        cells.append(f"{r['ret']:+7.1%} {r['dd']:6.1%} {r['n']:4}t {r['pf']:4.2f}")
    return f"{label:34} | " + " | ".join(cells)

hdr = f"{'variant':34} | " + " | ".join(f"{l:>25}" for _, l in WINDOWS)
lines = ["20 coins, max 5 open, 1% risk. Cells: return, max drawdown, trades, profit factor.\n", hdr]
lines.append(line('baseline (all 8 required, 5 of 8)', lambda: Opportunity(OppParams())))
lines.append("\n# A. stop requiring one check (it always counts as passed)")
for ck in CHECKS:
    lines.append(line(f"without {ck}", lambda ck=ck: Ablated(OppParams(), ck)))
lines.append("\n# B. threshold")
for ms in (4, 5, 6):
    lines.append(line(f"min_score {ms} of 8", lambda ms=ms: Opportunity(OppParams(min_score=ms))))
lines.append("\n# C. execution costs")
for fee, slip, label in ((0.001, 0.0005, 'fee 0.10% slip 0.05% (normal)'), (0.002, 0.001, 'fee 0.20% slip 0.10% (double)'),
                         (0.003, 0.0015, 'fee 0.30% slip 0.15% (triple)'), (0.0, 0.0, 'no costs (upper bound)')):
    lines.append(line(label, lambda: Opportunity(OppParams()), fee=fee, slip=slip))
open(f'{RES}/research7.md', 'w').write("\n".join(lines) + "\n")
print("\n".join(lines))
