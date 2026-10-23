"""Research round 20: a short side for bear markets.

The bot is long-only and lost money in 2018 (-14%), 2022 (-28%) and 2025
(-11%). Perpetual futures let a bot sell a coin it doesn't own and profit
when the price falls. Does a mirror image of the live rules make money on
the short side, and does it smooth the long book's bad years?

Short rules: exactly the live rules applied to the inverted price (1/price),
so every check flips: price below a falling 200-EMA, 20-EMA below 50-EMA,
MACD histogram falling, RSI 20-60, volume above average, the same
volatility band, a close below the 20-day low, and price within 1 ATR of the
20-EMA. Stop 2xATR above entry, trailing 3xATR above the lowest close, 1%
risk, sharing the same 5 slots as the longs (highest score first), checked
at the daily close and filled at the next open, like the longs.

Costs: the same 0.1% fee + 0.05% slippage per side as round 12, plus the
funding rate. Shorts receive it when positive, which is most of the time
in crypto. Daily funding comes from round 13's Binance data for the 20
coins it covers; other coins are charged zero, which is optimistic only
when funding was negative. Shorts are collateralised 1:1 (no leverage).

Variants: longs only (live), shorts only, both, and both with shorts allowed
only while BTC is below its 200-day EMA. Split check 2017-21 / 2022-26.
Same data, universe rule and survivorship caveat as round 12; the
survivorship bias works in favour of shorts here only if anything, since
the coins that collapsed and were delisted (LUNA, FTT) are missing.
"""
import math
import os as _os
import pickle
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research12.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r12'}
exec(src[:src.index('\nL = []')], ns)
data, quarters, rank_at, t0, QUARTER = ns['data'], ns['quarters'], ns['rank_at'], ns['t0'], ns['QUARTER']
FEE, SLIP, Opportunity, OppParams, btc_bull, d = (ns['FEE'], ns['SLIPPAGE'], ns['Opportunity'], ns['OppParams'],
                                                  ns['btc_bull'], ns['d'])
from tradebot.data import Candle

P = OppParams()
DAY = 86_400_000
inv = {s: [Candle(c.open_time, 1 / c.open, 1 / c.low, 1 / c.high, 1 / c.close, c.volume, c.close_time) for c in cs]
       for s, cs in data.items()}
fut = pickle.load(open(_os.path.join(HERE, '..', 'data', 'funding.pkl'), 'rb'))
funding = {c + 'USDT': f['funding'] for c, f in fut.items()}       # symbol -> {day: funding paid that day}


def run(longs=True, shorts=False, shorts_bear_only=False, top=15, fee=FEE, slip=SLIP, max_open=5, risk=0.01,
        capital=10000.0, start=None, end=None, use_funding=True):
    L_st = {s: Opportunity(P).prepare(cs) for s, cs in data.items()}
    S_st = {s: Opportunity(P).prepare(cs) for s, cs in inv.items()}
    idx = {s: {c.open_time: i for i, c in enumerate(cs)} for s, cs in data.items()}
    times = sorted(set(t for s in data for t in idx[s]))
    times = [t for t in times if (start is None or t >= start) and (end is None or t < end)]
    cash, pos, exits, orders, curve, trades = capital, {}, set(), {}, [], []
    fund_total = 0.0

    def mark(s, t):
        q = pos[s]; px = data[s][idx[s][t]].close
        return q['qty'] * px if q['side'] == 'L' else -q['qty'] * px

    def close_pos(s, px, t):
        nonlocal cash
        q = pos.pop(s)
        if q['side'] == 'L':
            cash += q['qty'] * px * (1 - fee); p = q['qty'] * px * (1 - fee) - q['cost']
        else:
            cost = q['qty'] * px * (1 + fee); cash -= cost; p = q['proceeds'] - cost
        trades.append(dict(t=t, pnl=p, r=p / q['risk'], sym=s, side=q['side']))

    last_eq = capital
    for t in times:
        eq_now = last_eq
        for s in list(exits):
            i = idx[s].get(t)
            if i is not None and s in pos:
                o = data[s][i].open
                close_pos(s, o * (1 - slip) if pos[s]['side'] == 'L' else o * (1 + slip), t)
                exits.discard(s)
        for s, o in sorted(orders.items(), key=lambda x: -x[1]['plan'].score):
            i = idx[s].get(t)
            if i is None or s in pos or len(pos) >= max_open:
                continue
            op = data[s][i].open
            if o['side'] == 'L':
                entry, stop = op * (1 + slip), o['plan'].stop
                if entry <= stop:
                    continue
                qty = min(eq_now * risk / (entry - stop), cash * (1 - fee) / entry)
                if qty > 0:
                    cash -= qty * entry / (1 - fee)
                    pos[s] = dict(side='L', qty=qty, cost=qty * entry / (1 - fee), stop=stop, risk=qty * (entry - stop))
            else:
                entry, stop = op * (1 - slip), 1 / o['plan'].stop          # stop above the price
                if entry >= stop:
                    continue
                # 1:1 collateral: total short notional never exceeds equity left over
                free = max(0.0, eq_now - sum(abs(mark(k, t)) if t in idx[k] else 0 for k in pos))
                qty = min(eq_now * risk / (stop - entry), free / entry)
                if qty > 0:
                    proceeds = qty * entry * (1 - fee); cash += proceeds
                    pos[s] = dict(side='S', qty=qty, proceeds=proceeds, stop=stop, risk=qty * (stop - entry))
        orders = {}
        qs = quarters[max(0, min(len(quarters) - 1, (t - t0) // QUARTER))]
        allowed = set(rank_at[qs][:top])
        bear = not btc_bull.get(t, False)
        for s, cs in data.items():
            i = idx[s].get(t)
            if i is None:
                continue
            c = cs[i]
            if s in pos:
                q = pos[s]
                if q['side'] == 'L':
                    if c.low <= q['stop']:
                        exits.add(s); continue
                    st = L_st[s]; st.peak = max(st.peak or 0, c.close)
                    q['stop'] = st.update_stop(i, q['stop'])
                else:
                    if use_funding:                  # shorts receive positive funding, pay negative
                        f = funding.get(s, {}).get(t // DAY * DAY, 0.0)
                        cash += f * q['qty'] * c.close; fund_total += f * q['qty'] * c.close
                    if c.high >= q['stop']:
                        exits.add(s); continue
                    st = S_st[s]; st.peak = max(st.peak or 0, 1 / c.close)
                    q['stop'] = 1 / st.update_stop(i, 1 / q['stop'])
            elif s in allowed:
                plan = L_st[s].signal(i) if longs else None
                if plan:
                    orders[s] = dict(side='L', plan=plan)
                elif shorts and (bear or not shorts_bear_only):
                    plan = S_st[s].signal(i)
                    if plan:
                        orders[s] = dict(side='S', plan=plan)
        eq = cash + sum(mark(k, t) for k in pos if t in idx[k])
        last_eq = eq
        curve.append((t, eq))
    return curve, trades, fund_total


def stats(curve, trades, side=None):
    eq = [e for _, e in curve]
    rets = [eq[i] / eq[i - 1] - 1 for i in range(1, len(eq))]
    pk = dd = 0
    for e in eq:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    mu = sum(rets) / len(rets); sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / len(rets))
    rs = [x['r'] for x in trades if side is None or x['side'] == side]
    tail = f"trades {len(rs):3d}  win {sum(r > 0 for r in rs) / max(1, len(rs)):4.0%}  avg {sum(rs) / max(1, len(rs)):+.2f}R"
    return f"{(eq[-1] / eq[0]) ** (365 / len(eq)) - 1:+6.1%}/yr  maxDD {dd:6.1%}  Sharpe {mu / sd * math.sqrt(365):4.2f}  {tail}"


def by_year(curve):
    out = {}
    for t, e in curve:
        out.setdefault(d(t)[:4], [e, e])[1] = e
    return {y: b / a - 1 for y, (a, b) in out.items()}


SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
cases = [("longs only (LIVE)", dict()),
         ("shorts only", dict(longs=False, shorts=True)),
         ("shorts only, BTC below 200-EMA", dict(longs=False, shorts=True, shorts_bear_only=True)),
         ("longs + shorts", dict(shorts=True)),
         ("longs + shorts (shorts only in BTC bear)", dict(shorts=True, shorts_bear_only=True))]
L = []
ref = ns['run']()
mine = run()
L.append(f"check: round 12 simulator {ns['metrics'](*ref)['cagr']:+.2%}/yr {len(ref[1])} trades; "
         f"this one, longs only: {(mine[0][-1][1] / 10000) ** (365 / len(mine[0])) - 1:+.2%}/yr {len(mine[1])} trades\n")
L.append("whole period 2017-08 -> 2026-10")
years = {}
for name, kw in cases:
    c, tr, f = run(**kw)
    years[name] = by_year(c)
    extra = f"   short trades: {stats(c, tr, 'S').split('  trades ')[1]}  funding received {f:+.0f}" if kw.get('shorts') else ""
    L.append(f"  {name:42s} {stats(c, tr)}{extra}")
L.append("\nby year")
L.append("  " + " " * 42 + "".join(f"{y:>8s}" for y in years[cases[0][0]]))
for name, ys in years.items():
    L.append(f"  {name:42s}" + "".join(f"{v:+8.1%}" for v in ys.values()))
L.append("\nsplit halves")
for name, kw in cases:
    a = run(end=SPLIT, **kw); b = run(start=SPLIT, **kw)
    L.append(f"  {name:42s} 2017-21: {stats(a[0], a[1])}")
    L.append(f"  {'':42s} 2022-26: {stats(b[0], b[1])}")
L.append("\nshorts without funding income (if funding had been zero)")
for name, kw in cases[1:]:
    c, tr, _ = run(use_funding=False, **kw)
    L.append(f"  {name:42s} {stats(c, tr)}")
print("\n".join(L))
