"""Research round 10: partial profit-taking, on the hindsight-free top-15-by-volume
universe (round 9). Sell a fraction of the position at k x initial risk (R),
move the stop on the rest to break-even, trail the remainder as usual."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')      # cached candles
RES = _os.path.join(HERE, '..', 'results')   # tables written here
import pickle, sys
sys.path.insert(0, ROOT)
from tradebot.opportunity import Opportunity, OppParams
from tradebot.backtest import FEE, SLIPPAGE
src = open(f'{HERE}/research9.py').read()
# reuse pool loading and quarterly ranking from round 9, without its experiments
ns = {}
exec(src.split("WINDOWS = ")[0], ns)
pool, top_n = ns['pool'], ns['top_n']


def portfolio(allowed, frac=0.0, at_r=2.0, be_stop=True, max_open=5, risk=0.01, capital=10000.0, start_frac=0.0):
    data = pool
    strats = {s: Opportunity(OppParams()).prepare(cs) for s, cs in data.items()}
    idx = {s: {c.open_time: i for i, c in enumerate(cs)} for s, cs in data.items()}
    times = sorted(set(t for s in data for t in idx[s]))
    start_t = times[int(len(times) * start_frac)]
    cash, pos, pending, curve, pnl_trades = capital, {}, {}, [], []
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
                entry = c.open * (1 + SLIPPAGE)
                qty = min(eq_now * risk / (entry - plan.stop), cash * (1 - FEE) / entry)
                if qty > 0:
                    cash -= qty * entry / (1 - FEE)
                    pos[s] = dict(qty=qty, entry=entry, stop=plan.stop, peak=entry, r=entry - plan.stop,
                                  partial=False, realised=-qty * entry / (1 - FEE))
            elif action == 'sell' and s in pos:
                q = pos[s]; px = c.open * (1 - SLIPPAGE)
                cash += q['qty'] * px * (1 - FEE)
                pnl_trades.append(q['realised'] + q['qty'] * px * (1 - FEE)); del pos[s]
        pending = {}
        for s, cs in data.items():
            i = idx[s].get(t)
            if i is None:
                continue
            c, st = cs[i], strats[s]
            if s in pos:
                q = pos[s]
                if c.low <= q['stop']:
                    px = min(q['stop'], c.open) * (1 - SLIPPAGE); cash += q['qty'] * px * (1 - FEE)
                    pnl_trades.append(q['realised'] + q['qty'] * px * (1 - FEE)); del pos[s]; continue
                target = q['entry'] + at_r * q['r']
                if frac > 0 and not q['partial'] and c.high >= target:
                    px = max(target, c.open) * (1 - SLIPPAGE)
                    sell = q['qty'] * frac
                    cash += sell * px * (1 - FEE); q['realised'] += sell * px * (1 - FEE)
                    q['qty'] -= sell; q['partial'] = True
                    if be_stop:
                        q['stop'] = max(q['stop'], q['entry'])
                st.peak = max(q['peak'], c.close); q['peak'] = st.peak
                q['stop'] = st.update_stop(i, q['stop'])
            elif allowed(s, t):
                plan = st.signal(i)
                if plan:
                    pending[s] = ('buy', plan)
        curve.append(eq_of(t))
    for s, q in pos.items():
        pnl_trades.append(q['realised'] + q['qty'] * data[s][-1].close * (1 - SLIPPAGE))
    final = curve[-1]; pk = dd = 0
    for e in curve:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    g = sum(x for x in pnl_trades if x > 0); l = -sum(x for x in pnl_trades if x <= 0)
    return dict(ret=final / capital - 1, dd=dd, n=len(pnl_trades),
                win=sum(x > 0 for x in pnl_trades) / max(1, len(pnl_trades)), pf=g / l if l else 99)


WINDOWS = [(0.0, 'full 4y'), (0.5, 'from 2024-10'), (0.7, 'from 2025-07'), (0.8, 'from 2025-12')]
allowed = top_n(15)
def line(label, **kw):
    cells = []
    for w, _ in WINDOWS:
        r = portfolio(allowed, start_frac=w, **kw)
        cells.append(f"{r['ret']:+7.1%} {r['dd']:6.1%} {r['win']:4.0%}w {r['pf']:4.2f}")
    return f"{label:40} | " + " | ".join(cells)

lines = ["Top 15 by volume (quarterly), max 5 open, 1% risk. Cells: return, max DD, win rate, PF.\n",
         f"{'exit variant':40} | " + " | ".join(f"{l:>25}" for _, l in WINDOWS)]
lines.append(line('baseline: trail only', frac=0.0))
for frac in (0.33, 0.5):
    for at_r in (1.5, 2.0, 3.0):
        lines.append(line(f'sell {frac:.0%} at {at_r}R, stop to break-even', frac=frac, at_r=at_r))
lines.append(line('sell 50% at 2R, stop NOT moved', frac=0.5, at_r=2.0, be_stop=False))
open(f'{RES}/research10.md', 'w').write("\n".join(lines) + "\n")
print("\n".join(lines))
