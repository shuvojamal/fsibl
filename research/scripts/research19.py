"""Research round 19: execution, not signals. How the bot buys and how its stops fire.

Same signals as the live rules; only the order handling changes.

A2. A backstop: keep the daily-close stop, and also rest a real stop order
   on the exchange x% below it, which only fires on a crash (or if the bot
   is down for days).

A. Stops. Live today: the bot checks once a day, and if the day's low
   touched the stop it sells at the next run (about the next open). The
   alternative is a real stop order resting on the exchange that fills the
   moment price touches the stop (at the stop, or at the open if the price
   gaps below it). It also protects the position if the bot fails to run.

B. Entries. Live today: market buy right after the signal close. The
   alternative is a limit buy k x ATR below the signal close, valid for N
   days, cancelled if not filled. It gets a better price but misses the
   trades that never pull back, which are often the strongest ones.

Same simulator, data, universe, costs and caveats as round 12 (its
simulator is re-implemented here with these two switches; the default
settings reproduce round 12's numbers exactly, which is checked below).
Split check on 2017-2021 and 2022-2026.
"""
import math
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research12.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r12'}
exec(src[:src.index('\nL = []')], ns)
data, quarters, rank_at, t0, QUARTER = ns['data'], ns['quarters'], ns['rank_at'], ns['t0'], ns['QUARTER']
FEE, SLIP, Opportunity, OppParams, d = ns['FEE'], ns['SLIPPAGE'], ns['Opportunity'], ns['OppParams'], ns['d']
P = OppParams()


def run(stop_mode='close', disaster=0.0, limit_atr=0.0, limit_days=1, top=15, fee=FEE, slip=SLIP, max_open=5, risk=0.01,
        capital=10000.0, start=None, end=None):
    strats = {s: Opportunity(P).prepare(cs) for s, cs in data.items()}
    idx = {s: {c.open_time: i for i, c in enumerate(cs)} for s, cs in data.items()}
    times = sorted(set(t for s in data for t in idx[s]))
    times = [t for t in times if (start is None or t >= start) and (end is None or t < end)]
    cash, pos, sells, orders, curve, trades = capital, {}, set(), {}, [], []
    missed = filled = 0

    def close_pos(s, px, t):
        nonlocal cash
        q = pos.pop(s)
        p = q['qty'] * px * (1 - fee) - q['cost']; cash += q['qty'] * px * (1 - fee)
        trades.append(dict(t=t, pnl=p, r=p / q['risk'], sym=s))

    for t in times:
        eq_now = curve[-1][1] if curve else capital
        for s in list(sells):                           # stop seen at yesterday's close: sell at the open
            i = idx[s].get(t)
            if i is not None and s in pos:
                close_pos(s, data[s][i].open * (1 - slip), t)
                sells.discard(s)
        # buys: market at the open (limit_atr == 0) or a resting limit order
        for s, o in sorted(orders.items(), key=lambda x: -x[1]['plan'].score):
            i = idx[s].get(t)
            if i is None or s in pos or len(pos) >= max_open:
                continue
            c = data[s][i]
            if limit_atr == 0:
                entry = c.open * (1 + slip)
            elif c.low <= o['limit']:
                entry = min(o['limit'], c.open)         # a limit fills at its price, or better on a gap down
            else:
                continue
            if entry <= o['plan'].stop:
                o['days'] = 0; continue
            qty = min(eq_now * risk / (entry - o['plan'].stop), cash * (1 - fee) / entry)
            if qty > 0:
                cash -= qty * entry / (1 - fee)
                pos[s] = dict(qty=qty, cost=qty * entry / (1 - fee), stop=o['plan'].stop, peak=entry,
                              risk=qty * (entry - o['plan'].stop))
                o['days'] = 0; filled += 1
        for s in list(orders):
            orders[s]['days'] -= 1
            if orders[s]['days'] <= 0:
                if s not in pos and limit_atr:
                    missed += 1
                del orders[s]
        qs = quarters[max(0, min(len(quarters) - 1, (t - t0) // QUARTER))]
        allowed = set(rank_at[qs][:top])
        for s, cs in data.items():
            i = idx[s].get(t)
            if i is None:
                continue
            c, st = cs[i], strats[s]
            if s in pos:
                q = pos[s]
                if disaster and c.low <= q['stop'] * (1 - disaster):
                    # backstop order resting on the exchange well below the daily-close stop
                    close_pos(s, min(q['stop'] * (1 - disaster), c.open) * (1 - slip), t)
                    continue
                if c.low <= q['stop']:
                    if stop_mode == 'intraday':         # resting stop order: filled today
                        close_pos(s, min(q['stop'], c.open) * (1 - slip), t)
                    else:                               # live behaviour: seen at the close, sold next open
                        sells.add(s)
                    continue
                st.peak = max(q['peak'], c.close); q['peak'] = st.peak
                q['stop'] = st.update_stop(i, q['stop'])
            elif s in allowed and s not in orders:
                plan = st.signal(i)
                if plan:
                    atr = (c.close - plan.stop) / P.stop_atr
                    orders[s] = dict(plan=plan, limit=c.close - limit_atr * atr, days=limit_days)
        eq = cash + sum(q['qty'] * data[k][idx[k][t]].close for k, q in pos.items() if t in idx[k])
        curve.append((t, eq))
    return curve, trades, filled, missed


def stats(curve, trades):
    eq = [e for _, e in curve]
    rets = [eq[i] / eq[i - 1] - 1 for i in range(1, len(eq))]
    yrs = len(eq) / 365
    pk = dd = 0
    for e in eq:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    mu = sum(rets) / len(rets); sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / len(rets))
    rs = [x['r'] for x in trades]
    return (f"{(eq[-1] / eq[0]) ** (1 / yrs) - 1:+6.1%}/yr  maxDD {dd:6.1%}  Sharpe {mu / sd * math.sqrt(365):4.2f}  "
            f"trades {len(rs):3d}  win {sum(r > 0 for r in rs) / len(rs):4.0%}  avg {sum(rs) / len(rs):+.2f}R")


SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
L = []
ref_curve, ref_trades = ns['run']()
mine = run()
L.append(f"check: round 12 simulator {ns['metrics'](ref_curve, ref_trades)['cagr']:+.2%}/yr, {len(ref_trades)} trades; "
         f"this one with live settings {(mine[0][-1][1] / 10000) ** (365 / len(mine[0])) - 1:+.2%}/yr, {len(mine[1])} trades\n")

cases = [
    ("LIVE: stop at close, market buy", dict()),
    ("A. exchange stop order (intraday)", dict(stop_mode='intraday')),
    ("A2. close stop + exchange backstop 5% lower", dict(disaster=0.05)),
    ("A2. close stop + exchange backstop 10% lower", dict(disaster=0.10)),
    ("A2. close stop + exchange backstop 20% lower", dict(disaster=0.20)),
    ("B. limit 0.25 ATR below, 1 day", dict(limit_atr=0.25, limit_days=1)),
    ("B. limit 0.5 ATR below, 1 day", dict(limit_atr=0.5, limit_days=1)),
    ("B. limit 0.5 ATR below, 3 days", dict(limit_atr=0.5, limit_days=3)),
    ("B. limit 1 ATR below, 3 days", dict(limit_atr=1.0, limit_days=3)),
    ("A+B. stop order + limit 0.5 ATR, 3 days", dict(stop_mode='intraday', limit_atr=0.5, limit_days=3)),
]
L.append(f"{'':44s} whole period 2017-08 -> 2026-10")
for name, kw in cases:
    c, tr, f, m = run(**kw)
    fill = f"  limit fills {f}, missed {m} ({m / max(1, f + m):.0%})" if kw.get('limit_atr') else ""
    L.append(f"  {name:42s} {stats(c, tr)}{fill}")
L.append("\nsplit halves")
for name, kw in cases:
    a = run(end=SPLIT, **kw); b = run(start=SPLIT, **kw)
    L.append(f"  {name:42s} 2017-21: {stats(a[0], a[1])}")
    L.append(f"  {'':42s} 2022-26: {stats(b[0], b[1])}")
print("\n".join(L))
