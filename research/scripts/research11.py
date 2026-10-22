"""Research round 11, top-15-by-volume universe (round 9), max 5 open, 1% risk:
  A. Slot allocation: when more coins signal than there are free slots, which
     to buy first? alphabetical (what the live bot did), by score, by trading
     volume, by momentum, or random (baseline, averaged over seeds).
  B. Stop execution: backtests so far filled a stop at the stop price (an
     exchange-side stop order). A bot that only checks once a day at the close
     sells at the close, or at the next open. How much does that cost?
"""
import os as _os
import random
import sys
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')
RES = _os.path.join(HERE, '..', 'results')
sys.path.insert(0, ROOT)
from tradebot.backtest import FEE, SLIPPAGE
from tradebot.opportunity import Opportunity, OppParams

ns = {'__file__': _os.path.join(HERE, 'research9.py')}
exec(open(_os.path.join(HERE, 'research9.py')).read().split("WINDOWS = ")[0], ns)
pool, top_n, rank_at, quarters, t0, QUARTER = (ns[k] for k in ('pool', 'top_n', 'rank_at', 'quarters', 't0', 'QUARTER'))
allowed = top_n(15)


def portfolio(order='pool', stop_fill='stop', seed=None, max_open=5, risk=0.01, capital=10000.0, start_frac=0.0):
    data = pool
    rng = random.Random(seed)
    strats = {s: Opportunity(OppParams()).prepare(cs) for s, cs in data.items()}
    idx = {s: {c.open_time: i for i, c in enumerate(cs)} for s, cs in data.items()}
    times = sorted(set(t for s in data for t in idx[s]))
    start_t = times[int(len(times) * start_frac)]
    cash, pos, pending, curve, pnl = capital, {}, {}, [], []
    eq_of = lambda t: cash + sum(q['qty'] * data[k][idx[k][t]].close for k, q in pos.items() if t in idx[k])

    def priority(s, plan, i, t):
        st = strats[s]
        if order == 'alpha':
            return s
        if order == 'score':
            return (-plan.score, s)
        if order == 'volume':
            qs = quarters[max(0, min(len(quarters) - 1, (t - t0) // QUARTER))]
            r = rank_at[qs]
            return r.index(s) if s in r else 999
        if order == 'momentum':   # 20-day return scaled by volatility: strongest trend first
            c = st.closes
            return -((c[i] / c[i - 20] - 1) / (st.atr[i] / c[i])) if i >= 20 and st.atr[i] else 0
        if order == 'random':
            return rng.random()
        return 0  # 'pool': dict order, as the earlier backtests did

    for t in times:
        if t < start_t:
            continue
        eq_now = curve[-1] if curve else capital
        # fills at this open; buys in priority order
        sells = [s for s, (a, _) in pending.items() if a in ('sell', 'stop_next_open')]
        for s in sells:
            i = idx[s].get(t)
            if i is None or s not in pos:
                continue
            px = data[s][i].open * (1 - SLIPPAGE); q = pos.pop(s)
            cash += q['qty'] * px * (1 - FEE); pnl.append(q['qty'] * px * (1 - FEE) - q['cost'])
        buys = [(s, p) for s, (a, p) in pending.items() if a == 'buy']
        buys.sort(key=lambda sp: sp[1][1])
        for s, (plan, _) in buys:
            i = idx[s].get(t)
            if i is None or s in pos or len(pos) >= max_open:
                continue
            entry = data[s][i].open * (1 + SLIPPAGE)
            qty = min(eq_now * risk / (entry - plan.stop), cash * (1 - FEE) / entry)
            if qty > 0:
                cash -= qty * entry / (1 - FEE)
                pos[s] = dict(qty=qty, cost=qty * entry / (1 - FEE), stop=plan.stop, peak=entry)
        pending = {}
        for s, cs in data.items():
            i = idx[s].get(t)
            if i is None:
                continue
            c, st = cs[i], strats[s]
            if s in pos:
                q = pos[s]
                if c.low <= q['stop']:
                    if stop_fill == 'stop':          # exchange-side stop order
                        px = min(q['stop'], c.open) * (1 - SLIPPAGE)
                    elif stop_fill == 'close':       # bot checks at the daily close, sells then
                        px = c.close * (1 - SLIPPAGE)
                    else:                            # 'next_open': sells at the next run
                        pending[s] = ('stop_next_open', None); continue
                    pos.pop(s); cash += q['qty'] * px * (1 - FEE); pnl.append(q['qty'] * px * (1 - FEE) - q['cost'])
                    continue
                st.peak = max(q['peak'], c.close); q['peak'] = st.peak
                q['stop'] = st.update_stop(i, q['stop'])
            elif allowed(s, t):
                plan = st.signal(i)
                if plan:
                    pending[s] = ('buy', (plan, priority(s, plan, i, t)))
        curve.append(eq_of(t))
    final = curve[-1]; pk = dd = 0
    for e in curve:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    g = sum(x for x in pnl if x > 0); l = -sum(x for x in pnl if x <= 0)
    return dict(ret=final / capital - 1, dd=dd, pf=g / l if l else 99, n=len(pnl))


WINDOWS = [(0.0, 'full 4y'), (0.5, 'from 2024-10'), (0.7, 'from 2025-07'), (0.8, 'from 2025-12')]
def line(label, **kw):
    cells = []
    for w, _ in WINDOWS:
        r = portfolio(start_frac=w, **kw)
        cells.append(f"{r['ret']:+7.1%} {r['dd']:6.1%} {r['pf']:4.2f}")
    return f"{label:38} | " + " | ".join(cells)

def random_line(seeds=10, **kw):
    cells = []
    for w, _ in WINDOWS:
        rs = [portfolio(order='random', seed=k, start_frac=w, **kw) for k in range(seeds)]
        rets = sorted(r['ret'] for r in rs)
        cells.append(f"{sum(rets)/len(rets):+7.1%} [{rets[0]:+.0%}..{rets[-1]:+.0%}]")
    return f"{'random order (10 seeds: mean [min..max])':38} | " + " | ".join(cells)

lines = ["Top 15 by volume, max 5 open, 1% risk. Cells: return, max DD, profit factor.\n",
         f"{'variant':38} | " + " | ".join(f"{l:>20}" for _, l in WINDOWS),
         "# A. which signal gets a free slot (stops fill at the stop price)"]
for order, label in (('pool', 'pool order (earlier backtests)'), ('alpha', 'alphabetical (live bot until now)'),
                     ('score', 'highest score first'), ('volume', 'most-traded first'),
                     ('momentum', 'strongest 20-day trend first')):
    lines.append(line(label, order=order))
lines.append(random_line())
lines.append("\n# B. stop execution (alphabetical order)")
for fill, label in (('stop', 'exchange stop order (fills at stop)'), ('close', 'checked at daily close'),
                    ('next_open', 'checked next morning (sells at open)')):
    lines.append(line(label, order='alpha', stop_fill=fill))
out = "\n".join(lines) + "\n"
open(_os.path.join(RES, 'research11.out'), 'w').write(out)
print(out)
