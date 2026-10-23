"""Research round 14: cross-sectional momentum (relative-strength rotation).

A different kind of opportunity from the trend bot's per-coin checks: every
week, rank the 15 most-traded coins by how much they rose over the last L
days, and hold the strongest N in equal weights. A coin is only held if its
own return is positive (absolute momentum), otherwise that slot stays in
cash. Variant: go fully to cash when BTC is below its 200-day EMA.

Decided at the daily close, filled at the next day's open, fee 0.1% +
slippage 0.05% on the traded amount. Same data, universe rule (top 15 by
trailing-90-day dollar volume, re-ranked quarterly) and survivorship caveat
as round 12, whose helpers this script reuses.

Questions:
  1. Does rotation make money after costs, and does it hold on unseen data
     (tune on 2017-08..2021-12, test 2022..2026)?
  2. How does it compare with the current trend bot on the same data?
  3. Is it different enough that running both (50/50) improves the
     combined result? (correlation of daily returns, blended Sharpe/drawdown)
"""
import itertools
import math
import os as _os
import sys
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research12.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r12'}
exec(src[:src.index('\nL = []')], ns)   # data, run (trend bot), metrics, quarters, rank_at, btc ...
data, run_trend, quarters, rank_at, t0, QUARTER = ns['data'], ns['run'], ns['quarters'], ns['rank_at'], ns['t0'], ns['QUARTER']
btc_bull, d = ns['btc_bull'], ns['d']
FEE, SLIP = ns['FEE'], ns['SLIPPAGE']

DAY = 86_400_000
idx = {s: {c.open_time: i for i, c in enumerate(cs)} for s, cs in data.items()}
TIMES = sorted(set(t for s in data for t in idx[s]))
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def close(s, t):
    i = idx[s].get(t)
    return data[s][i].close if i is not None else None


def past_return(s, t, look):
    a, b = close(s, t - look * DAY), close(s, t)
    return b / a - 1 if a and b else None


def rotate(look=30, n=5, every=7, regime=False, top=15, start=None, end=None, cost=FEE + SLIP, capital=10000.0):
    times = [t for t in TIMES if (start is None or t >= start) and (end is None or t < end)]
    cash, qty, pending, curve, turnover = capital, {}, None, [], 0.0
    for k, t in enumerate(times):
        if pending is not None:                       # fill yesterday's decision at today's open
            opens = {s: data[s][idx[s][t]].open for s in set(qty) | set(pending) if t in idx[s]}
            eq = cash + sum(q * opens.get(s, close(s, t) or 0) for s, q in qty.items())
            for s in sorted(set(qty) | set(pending), key=lambda s: pending.get(s, 0)):   # sells first
                if s not in opens:
                    continue
                want = eq * pending.get(s, 0) / opens[s]
                diff = want - qty.get(s, 0)
                if abs(diff) * opens[s] < eq * 0.01:  # skip trades under 1% of equity
                    continue
                cash -= diff * opens[s] + abs(diff) * opens[s] * cost
                turnover += abs(diff) * opens[s]
                qty[s] = want
                if qty[s] <= 1e-12:
                    qty.pop(s)
            pending = None
        eq = cash + sum(q * (close(s, t) or 0) for s, q in qty.items())
        curve.append((t, eq))
        if k % every == 0:
            qs = quarters[max(0, min(len(quarters) - 1, (t - t0) // QUARTER))]
            pool = [s for s in rank_at[qs][:top] if t in idx[s]]
            ranked = sorted(((past_return(s, t, look), s) for s in pool), key=lambda x: -(x[0] if x[0] is not None else -9))
            picks = [s for r, s in ranked[:n] if r is not None and r > 0]
            if regime and not btc_bull.get(t, False):
                picks = []
            pending = {s: 1 / n for s in picks}
    return curve, turnover


def stats(curve, capital=10000.0):
    eq = [e for _, e in curve]
    rets = [eq[i] / eq[i - 1] - 1 for i in range(1, len(eq))]
    yrs = len(eq) / 365
    pk = dd = 0
    for e in eq:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    mu = sum(rets) / len(rets); sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / len(rets))
    cagr = (eq[-1] / eq[0]) ** (1 / yrs) - 1
    return dict(cagr=cagr, dd=dd, sharpe=mu / sd * math.sqrt(365) if sd else 0, calmar=cagr / -dd if dd else 0, rets=rets)


def line(name, s, extra=""):
    return f"{name:42s} {s['cagr']:+7.1%}/yr  maxDD {s['dd']:6.1%}  Sharpe {s['sharpe']:4.2f}  Calmar {s['calmar']:4.2f}{extra}"


def by_year(curve):
    out = {}
    for t, e in curve:
        out.setdefault(d(t)[:4], [e, e])[1] = e
    return {y: b / a - 1 for y, (a, b) in out.items()}


L = []
L.append(f"Pool {len(data)} coins, {d(TIMES[0])} -> {d(TIMES[-1])}; top 15 by 90-day volume; split at 2022-01-01\n")

L.append("## 1. Grid: lookback x holdings x rebalance, first half (tuning) and second half (unseen)")
mean = lambda v: sum(v) / len(v)
rows = []
for look, n, every, regime in itertools.product([14, 30, 60, 90], [3, 5], [7, 14], [False, True]):
    a = stats(rotate(look, n, every, regime, end=SPLIT)[0])
    b = stats(rotate(look, n, every, regime, start=SPLIT)[0])
    rows.append((a['sharpe'], look, n, every, regime, a, b))
    L.append(f"  look {look:2d}d hold {n} every {every:2d}d {'BTC-filter' if regime else '          '}  "
             f"train {a['cagr']:+7.1%}/yr DD {a['dd']:6.1%} Sh {a['sharpe']:4.2f}  |  unseen {b['cagr']:+7.1%}/yr DD {b['dd']:6.1%} Sh {b['sharpe']:4.2f}")
rows.sort(key=lambda r: -r[0])
_, LK, N, EV, RG, a, b = rows[0]
L.append(f"\nBest on training by Sharpe: look {LK}d, hold {N}, every {EV}d, BTC filter {RG}")
L.append(line("  training", a)); L.append(line("  unseen", b))
tr_sh = [r[5]['sharpe'] for r in rows]; un_sh = [r[6]['sharpe'] for r in rows]
L.append(f"  all 64 settings: unseen Sharpe median {sorted(un_sh)[len(un_sh) // 2]:.2f}, "
         f"{sum(s > 0 for s in un_sh)} of 64 positive; training median {sorted(tr_sh)[len(tr_sh) // 2]:.2f}")
rk = lambda v: [sorted(v).index(x) for x in v]
ra, rb = rk(tr_sh), rk(un_sh)
L.append(f"  rank correlation train vs unseen Sharpe: {sum((x - mean(ra)) * (y - mean(rb)) for x, y in zip(ra, rb)) / math.sqrt(sum((x - mean(ra)) ** 2 for x in ra) * sum((y - mean(rb)) ** 2 for y in rb)):+.2f}")

L.append("\n## 2. Whole period: rotation vs the trend bot vs BTC")
rc, turn = rotate(LK, N, EV, RG)
rs = stats(rc)
tc, trades = run_trend()
ts = stats(tc)
b0 = next(i for i, c in enumerate(ns['btc']) if c.open_time >= rc[0][0])
bc = [(c.open_time, c.close) for c in ns['btc'][b0:]]
bs = stats(bc)
L.append(line(f"rotation (look {LK}, hold {N}, every {EV}, filter {RG})", rs, f"  traded {turn / mean([e for _, e in rc]):.0f}x its average equity"))
L.append(line("trend bot (current live rules)", ts))
L.append(line("buy & hold BTC", bs))
ry, ty, byy = by_year(rc), by_year(tc), by_year(bc)
L.append("  year   rotation   trend bot   BTC")
for y in ry:
    L.append(f"  {y}   {ry[y]:+8.1%}   {ty.get(y, 0):+8.1%}   {byy.get(y, 0):+8.1%}")

L.append("\n## 3. Running both: 50/50, rebalanced daily")
tmap = dict(tc); rmap = dict(rc)
common = [t for t in sorted(tmap) if t in rmap]
r1 = [rmap[common[i]] / rmap[common[i - 1]] - 1 for i in range(1, len(common))]
r2 = [tmap[common[i]] / tmap[common[i - 1]] - 1 for i in range(1, len(common))]
m1, m2 = mean(r1), mean(r2)
corr = sum((x - m1) * (y - m2) for x, y in zip(r1, r2)) / math.sqrt(sum((x - m1) ** 2 for x in r1) * sum((y - m2) ** 2 for y in r2))
L.append(f"correlation of daily returns, rotation vs trend bot: {corr:+.2f}")
for w in (0.0, 0.25, 0.5, 0.75, 1.0):
    eq, cv = 10000.0, [(common[0], 10000.0)]
    for i, t in enumerate(common[1:]):
        eq *= 1 + w * r1[i] + (1 - w) * r2[i]; cv.append((t, eq))
    L.append(line(f"  {w:.0%} rotation / {1 - w:.0%} trend bot", stats(cv)))
for half, (s, e) in (("first half", (None, SPLIT)), ("second half", (SPLIT, None))):
    ts_ = [t for t in common if (s is None or t >= s) and (e is None or t < e)]
    for w in (0.0, 0.5):
        eq, cv = 10000.0, [(ts_[0], 10000.0)]
        for t_prev, t in zip(ts_, ts_[1:]):
            eq *= 1 + w * (rmap[t] / rmap[t_prev] - 1) + (1 - w) * (tmap[t] / tmap[t_prev] - 1); cv.append((t, eq))
        L.append(line(f"  {half}: {w:.0%} rotation", stats(cv)))

L.append("\n## 4. Cost stress on the chosen rotation (unseen half)")
for c in (FEE + SLIP, 2 * (FEE + SLIP), 3 * (FEE + SLIP)):
    L.append(line(f"  cost {c:.2%} per side", stats(rotate(LK, N, EV, RG, start=SPLIT, cost=c)[0])))

out = "\n".join(L)
print(out)
