"""Research round 23: the cost of a late run, and whether the 2% price guard helps.

The live bots decide on the 00:00 UTC daily close but run later: the GitHub
job often starts about 4 hours late, a manual "Run now" can be 17 hours
late, and the VPS runs within minutes. Since round 21's change, the bot
also skips a buy when the exchange price is more than 2% away from the
signal candle's close (the bad-data guard, which in practice also stops it
chasing a coin that already ran).

Questions, decided before running:
  1. How much worse is entering d hours after the close (d = 0, 4, 8, 12, 16)?
  2. With the guard (skip the buy if the entry price is more than 2% above
     the signal close; also 1%, 3%, 5%), is a late run better or worse
     than without it?
  Pass bar for keeping the 2% guard: at the delays the live bots really
  have (0 and 4 h), it must not cost more than 1 percentage point a year
  against no guard, in both halves.

Method: round 21's cached daily candles (30 coins, rebuilt from hourly
data). Signals, universe and exits come from the 00:00 candles exactly as
in round 12. Only the entry price changes: a run d hours after the close
buys at the price d hours into the next day, which is the open of round
21's offset-d candle. Same costs (0.1% fee + 0.05% slippage). Split halves
2018-21 / 2022-26.
"""
import math
import os as _os
import pickle
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r23'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, DAY, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['DAY'], ns21['ROOT']

# round 12's universe machinery on the 00:00 candles
data0 = unpack(raw[0])
pk = _os.path.join(ROOT, 'research', 'data', '_r23_tmp.pkl')
pickle.dump(data0, open(pk, 'wb'))
src12 = open(_os.path.join(HERE, 'research12.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r23b'}
exec(src12[:src12.index('\nL = []')].replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
_os.remove(pk)
data, quarters, rank_at, t0, QUARTER = ns['data'], ns['quarters'], ns['rank_at'], ns['t0'], ns['QUARTER']
FEE, SLIP, Opportunity, OppParams = ns['FEE'], ns['SLIPPAGE'], ns['Opportunity'], ns['OppParams']
P = OppParams()

# price d hours after each 00:00 boundary = open of the offset-d candle starting then
open_at = {o: {s: {ts: float(vals[5 * i]) for i, ts in enumerate(tsa)} for s, (tsa, vals) in raw[o].items()} for o in OFFSETS}


def run(delay=0, guard=None, start=None, end=None, top=15, max_open=5, risk=0.01, capital=10000.0):
    strats = {s: Opportunity(P).prepare(cs) for s, cs in data.items()}
    idx = {s: {c.open_time: i for i, c in enumerate(cs)} for s, cs in data.items()}
    times = sorted(set(t for s in data for t in idx[s]))
    times = [t for t in times if (start is None or t >= start) and (end is None or t < end)]
    cash, pos, sells, orders, curve, trades = capital, {}, set(), {}, [], []
    skipped = taken = 0
    for t in times:
        eq_now = curve[-1][1] if curve else capital
        for s in list(sells):
            i = idx[s].get(t)
            if i is not None and s in pos:
                px = data[s][i].open * (1 - SLIP); q = pos.pop(s)
                p = q['qty'] * px * (1 - FEE) - q['cost']; cash += q['qty'] * px * (1 - FEE)
                trades.append(p / q['risk']); sells.discard(s)
        for s, o in sorted(orders.items(), key=lambda x: -x[1]['plan'].score):
            if s in pos or len(pos) >= max_open:
                continue
            raw_px = open_at[delay].get(s, {}).get(t + delay * H)
            if raw_px is None:
                continue
            if guard is not None and raw_px / o['close'] - 1 > guard:
                skipped += 1
                continue
            entry = raw_px * (1 + SLIP)
            if entry <= o['plan'].stop:
                continue
            qty = min(eq_now * risk / (entry - o['plan'].stop), cash * (1 - FEE) / entry)
            if qty > 0:
                cash -= qty * entry / (1 - FEE); taken += 1
                pos[s] = dict(qty=qty, cost=qty * entry / (1 - FEE), stop=o['plan'].stop, peak=entry,
                              risk=qty * (entry - o['plan'].stop))
        orders = {}
        qs = quarters[max(0, min(len(quarters) - 1, (t - t0) // QUARTER))]
        allowed = set(rank_at[qs][:top])
        for s, cs in data.items():
            i = idx[s].get(t)
            if i is None:
                continue
            c, st = cs[i], strats[s]
            if s in pos:
                q = pos[s]
                if c.low <= q['stop']:
                    sells.add(s); continue
                st.peak = max(q['peak'], c.close); q['peak'] = st.peak
                q['stop'] = st.update_stop(i, q['stop'])
            elif s in allowed:
                plan = st.signal(i)
                if plan:
                    orders[s] = dict(plan=plan, close=c.close)
        curve.append((t, cash + sum(q['qty'] * data[k][idx[k][t]].close for k, q in pos.items() if t in idx[k])))
    eq = [e for _, e in curve]
    rets = [eq[i] / eq[i - 1] - 1 for i in range(1, len(eq))]
    pk_ = dd = 0
    for e in eq:
        pk_ = max(pk_, e); dd = min(dd, e / pk_ - 1)
    mu = sum(rets) / len(rets); sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / len(rets))
    return dict(cagr=(eq[-1] / eq[0]) ** (365 / len(eq)) - 1, dd=dd, sharpe=mu / sd * math.sqrt(365),
                n=len(trades), avg_r=sum(trades) / max(1, len(trades)), skipped=skipped, taken=taken)


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
fmt = lambda m: f"{m['cagr']:+6.1%}/yr  DD {m['dd']:6.1%}  Sh {m['sharpe']:4.2f}  trades {m['n']:3d}  avg {m['avg_r']:+.2f}R"
L = ["30 coins, signals on the 00:00 UTC close, entry d hours later; scored from 2018-03\n"]
L.append("## 1. Delay, no guard vs the live 2% guard")
for d in OFFSETS:
    a = run(d, None, start=START); b = run(d, 0.02, start=START)
    L.append(f"  {d:2d} h late  no guard: {fmt(a)}")
    L.append(f"            2% guard: {fmt(b)}   (buys skipped {b['skipped']}, taken {b['taken']})")
L.append("\n## 2. Guard size at the live delays")
for d in (0, 4):
    for g in (None, 0.01, 0.02, 0.03, 0.05):
        m = run(d, g, start=START)
        L.append(f"  {d} h late, guard {'none' if g is None else f'{g:.0%}':>4s}: {fmt(m)}   skipped {m['skipped']}")
L.append("\n## 3. Split halves, live delays, no guard vs 2%")
for d in (0, 4):
    for g in (None, 0.02):
        a = run(d, g, start=START, end=SPLIT); b = run(d, g, start=SPLIT)
        L.append(f"  {d} h, guard {'none' if g is None else '2%':>4s}  2018-21: {fmt(a)}")
        L.append(f"  {'':16s}  2022-26: {fmt(b)}")
print("\n".join(L))
