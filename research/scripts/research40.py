"""Research round 40: slow quarterly investing on DSE (hold good shares for months).

Round 38 found the bot's daily trend rules lose money on DSE (costs vs tight
stops). The owner prefers a slow, quarterly approach that collects bonus
shares, dividends and capital gains, noting some DSE shares made ~30% a year
for 5-10 years.

Data: round 38's cached adjusted DSE prices (Mendeley doi:10.17632/23553sm4tn.4,
CC BY 4.0), 2012-10 .. 2026-01. Adjusted for bonus shares and splits but
NOT for cash dividends (checked: GP, a cash-only payer, has no adjustments
after 2020), so all returns here are price + bonus; real returns are higher
by the dividend yield (often 3-6%/yr). DSEX is a price index, so the same
omission applies to the benchmark.

Method (decided before running):
  - Rebalance on the first trading day of Jan/Apr/Jul/Oct, at that day's
    open, using only data up to the previous close.
  - Universe each quarter: the 50 equities with the highest traded value
    over the previous ~6 months that traded on at least 80% of those days
    and have a year of history (liquid shares only).
  - Equal weight, held for the quarter. Costs 0.40% brokerage + 0.30%
    slippage on every taka bought or sold.
  - Strategies: momentum (return over the last 12 months skipping the
    latest month, "12-1"), 6-month momentum, low volatility (lowest daily
    swings over 6 months), momentum + low volatility combined, and momentum
    with a market filter (cash for the quarter while DSEX is below its
    200-day average). Benchmarks: holding DSEX, and an equal-weight basket
    of the whole 50-share universe (same rebalancing and costs).
  - Halves: 2013-10 .. 2019 and 2020 .. 2026-01.

Primary strategy, chosen before running: 12-1 momentum, top 10.
Pass bar: the primary strategy must beat BOTH DSEX and the equal-weight
universe in yearly return in both halves, after costs, with a worst drop no
more than 5 points deeper than DSEX's in each half. Eight variants are
tried, so a lone variant passing would be weak evidence.

Also reported: how many DSE shares actually made 30%+ a year over the last
5 and 10 years (price + bonus), and the top ten (hindsight: picking them
in advance is the hard part).
"""
import gzip
import math
import os as _os
import pickle
import sys
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
raw = pickle.load(gzip.open(_os.path.join(ROOT, 'research', 'data', 'dse_daily_adj.pkl.gz')))

DAY = 86_400_000
day = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc)
ms = lambda y, m, d: int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)

# per share: {time: (open, close, volume)}
S = {}
for s, (ts, v) in raw.items():
    S[s] = {t: (float(v[5 * i]), float(v[5 * i + 3]), float(v[5 * i + 4])) for i, t in enumerate(ts)}
dsex = S.pop("00DSEX")
CAL = sorted(dsex)                                  # trading calendar from the index
POS = {t: i for i, t in enumerate(CAL)}
FEE = 0.007                                         # 0.40% + 0.30% per side


def last_close(s, i):
    """Latest close of share s on or before calendar index i (None if it had not listed)."""
    d = S[s]
    for k in range(i, max(-1, i - 30), -1):
        if CAL[k] in d:
            return d[CAL[k]][1]
    return None


def closes_window(s, i, n):
    d = S[s]
    return [d[CAL[k]][1] for k in range(max(0, i - n), i + 1) if CAL[k] in d]


def universe(i):
    out = []
    for s, d in S.items():
        days = [CAL[k] for k in range(max(0, i - 126), i + 1) if CAL[k] in d]
        if len(days) < 0.8 * 126 or sum(1 for t in d if t <= CAL[i]) < 252:
            continue
        out.append((sum(d[t][1] * d[t][2] for t in days), s))
    return [s for _, s in sorted(out, reverse=True)[:50]]


def mom(s, i, look, skip):
    c = closes_window(s, i, look + skip)
    if len(c) < 0.8 * (look + skip):
        return None
    return c[-1 - skip] / c[0] - 1 if skip else c[-1] / c[0] - 1


def vol(s, i):
    c = closes_window(s, i, 126)
    r = [c[k] / c[k - 1] - 1 for k in range(1, len(c))]
    if len(r) < 60:
        return None
    m = sum(r) / len(r)
    return math.sqrt(sum((x - m) ** 2 for x in r) / len(r))


def pick(kind, i, uni, n):
    if kind == "equal":
        return uni
    if kind in ("mom12", "mom12_filter"):
        sc = {s: mom(s, i, 231, 21) for s in uni}
    elif kind == "mom6":
        sc = {s: mom(s, i, 126, 0) for s in uni}
    elif kind == "lowvol":
        sc = {s: -v for s in uni if (v := vol(s, i)) is not None}
    elif kind == "combo":
        m = {s: x for s in uni if (x := mom(s, i, 231, 21)) is not None}
        v = {s: x for s in uni if (x := vol(s, i)) is not None}
        both = [s for s in m if s in v]
        rm = {s: k for k, s in enumerate(sorted(both, key=lambda s: -m[s]))}
        rv = {s: k for k, s in enumerate(sorted(both, key=lambda s: v[s]))}
        sc = {s: -(rm[s] + rv[s]) for s in both}
    sc = {s: x for s, x in sc.items() if x is not None}
    return sorted(sc, key=lambda s: -sc[s])[:n]


def dsex_ok(i):
    c = [dsex[CAL[k]][1] for k in range(max(0, i - 199), i + 1)]
    return c[-1] >= sum(c) / len(c)


def backtest(kind, n, start, end):
    i0 = next(k for k, t in enumerate(CAL) if t >= start)
    i1 = len(CAL) if end is None else next(k for k, t in enumerate(CAL) if t >= end)
    rebal = {k for k in range(i0, i1) if k == i0 or day(CAL[k]).month != day(CAL[k - 1]).month and day(CAL[k]).month in (1, 4, 7, 10)}
    cash, hold, curve = 10000.0, {}, []           # hold: share -> number of shares
    for k in range(i0, i1):
        t = CAL[k]
        if k in rebal:
            uni = universe(k - 1)
            want = [] if kind == "mom12_filter" and not dsex_ok(k - 1) else pick(kind, k - 1, uni, n)
            px = {s: (S[s][t][0] if t in S[s] and S[s][t][0] > 0 else last_close(s, k - 1)) for s in set(hold) | set(want)}
            value = cash + sum(q * px[s] for s, q in hold.items() if px[s])
            target = {s: value / len(want) for s in want if px[s]} if want else {}
            for s in list(hold):                    # sell what's not wanted or overweight
                cur = hold[s] * px[s]
                tgt = target.get(s, 0.0)
                if cur > tgt:
                    sell = cur - tgt
                    cash += sell * (1 - FEE); hold[s] -= sell / px[s]
                    if hold[s] * px[s] < 1:
                        del hold[s]
            for s, tgt in target.items():           # buy up to target
                cur = hold.get(s, 0.0) * px[s]
                if tgt > cur:
                    buy = min(tgt - cur, cash / (1 + FEE))
                    cash -= buy * (1 + FEE); hold[s] = hold.get(s, 0.0) + buy / px[s]
        eq = cash + sum(q * (last_close(s, k) or 0.0) for s, q in hold.items())
        curve.append((t, eq))
    return curve


def stats(curve):
    eq = [e for _, e in curve]
    yrs = len(eq) / 245                                # DSE trades ~245 days a year
    r = [eq[k] / eq[k - 1] - 1 for k in range(1, len(eq))]
    m = sum(r) / len(r); sd = math.sqrt(sum((x - m) ** 2 for x in r) / len(r))
    pk, dd = eq[0], 0.0
    for e in eq:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    return dict(cagr=(eq[-1] / eq[0]) ** (1 / yrs) - 1, sharpe=m / sd * math.sqrt(245) if sd else 0, dd=dd)


HALVES = [("2013-10..2019", ms(2013, 10, 1), ms(2020, 1, 1)), ("2020..2026-01", ms(2020, 1, 1), None)]
CASES = [("PRIMARY momentum 12-1, top 10", "mom12", 10), ("momentum 12-1, top 5", "mom12", 5), ("momentum 12-1, top 20", "mom12", 20),
         ("momentum 6 months, top 10", "mom6", 10), ("low volatility, top 10", "lowvol", 10),
         ("momentum + low vol, top 10", "combo", 10), ("momentum 12-1 + DSEX filter", "mom12_filter", 10),
         ("equal-weight universe (50)", "equal", 50)]
res = {}
L = ["Quarterly rebalanced DSE portfolios, top-50 liquid universe, costs 0.7% per side; price + bonus (cash dividends excluded)\n",
     f"{'strategy':32s} | " + " | ".join(f"{h:^30s}" for h, _, _ in HALVES),
     f"{'':32s} | " + " | ".join(f"{'ret/yr':>9s} {'Sharpe':>7s} {'maxDD':>8s}  " for _ in HALVES)]
for name, kind, n in CASES:
    row = f"{name:32s} |"
    for h, s, e in HALVES:
        m = stats(backtest(kind, n, s, e)); res[(name, h)] = m
        row += f" {m['cagr']:+9.1%} {m['sharpe']:7.2f} {m['dd']:8.1%}   |"
    L.append(row)
row = f"{'hold DSEX (price index)':32s} |"
for h, s, e in HALVES:
    m = stats([(t, dsex[t][1]) for t in CAL if t >= s and (e is None or t < e)]); res[("DSEX", h)] = m
    row += f" {m['cagr']:+9.1%} {m['sharpe']:7.2f} {m['dd']:8.1%}   |"
L.append(row)

P, EW = CASES[0][0], "equal-weight universe (50)"
checks = []
for h, _, _ in HALVES:
    checks.append((f"beats DSEX, {h}", res[(P, h)]['cagr'] > res[("DSEX", h)]['cagr']))
    checks.append((f"beats the equal-weight universe, {h}", res[(P, h)]['cagr'] > res[(EW, h)]['cagr']))
    checks.append((f"worst drop within 5 pts of DSEX, {h}", res[(P, h)]['dd'] >= res[("DSEX", h)]['dd'] - 0.05))
L += [""] + [f"  {'PASS' if ok else 'FAIL'}  {t}" for t, ok in checks]
L.append(f"verdict for the primary strategy: {'PASS' if all(ok for _, ok in checks) else 'FAIL'}")
others = [n for n, k, _ in CASES[1:-1] if all(res[(n, h)]['cagr'] > max(res[('DSEX', h)]['cagr'], res[(EW, h)]['cagr']) for h, _, _ in HALVES)]
L.append(f"variants beating both benchmarks in both halves: {', '.join(others) or 'none'}")

# How many shares really made 30%+ a year? (hindsight, price + bonus)
L += ["", "Shares with 30%+ a year (price + bonus, to 2026-01; hindsight):"]
end_t = CAL[-1]
for yrs, y0 in ((5, 2021), (10, 2016)):
    t0 = next(t for t in CAL if t >= ms(y0, 1, 22))
    got = []
    for s, d in S.items():
        if t0 in d and end_t in d and d[t0][1] > 0:
            got.append(((d[end_t][1] / d[t0][1]) ** (1 / yrs) - 1, s))
    got.sort(reverse=True)
    n30 = sum(1 for g, _ in got if g >= 0.30)
    L.append(f"  {yrs} years: {n30} of {len(got)} shares ({n30 / len(got):.0%}); median share {sorted(g for g, _ in got)[len(got) // 2]:+.1%}/yr; "
             f"top: " + ", ".join(f"{s} {g:+.0%}" for g, s in got[:10]))
print("\n".join(L))
