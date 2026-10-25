"""Research round 41: can a rule pick "quality" DSE shares in advance?

The owner named BRAC Bank, Uttara Bank, Kohinoor, Square Pharma, Marico and
Ibn Sina as the kind of shares they want: long-established companies that
grew steadily for years (10-year price + bonus CAGR of 2-16% to 2026, vs
+0.9% for DSEX). Naming them today uses hindsight. The question is whether a
simple rule, using only information available at the time, would have
picked shares like them.

Quality screen (no fundamentals in the data, so price behaviour stands in):
each January, among equities with 5+ years of history that are in the top
100 by traded value over the last year, score each share on
  - 5-year price + bonus CAGR (steady long-term growth), and
  - consistency: the share of the last 5 calendar years with a gain, and
  - the worst drop over the last 3 years (shallower is better),
rank on each, add the ranks, buy the best 10 in equal amounts and hold for
a year (annual rebalancing keeps costs low). Variants: top 5 and 20;
6-monthly rebalancing. Data, costs (0.7%/side), calendar and price rules as
round 40; returns exclude cash dividends, as does DSEX.

Pass bar, decided before running: the primary (top 10, yearly) must beat
DSEX in yearly return in both halves (2013-10..2019, 2020..2026-01) with a
worst drop no more than 5 points deeper than DSEX's. Also reported: what the
owner's six shares did as an equal-weight basket (hindsight, for scale), and
which shares the screen held most often.
"""
import os as _os
import collections

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research40.py')).read()
g = {'__file__': _os.path.join(HERE, 'research40.py'), '__name__': 'r41'}
exec(src[:src.index('\nHALVES = [')], g)
S, CAL, dsex, FEE, last_close, stats, ms, day = g['S'], g['CAL'], g['dsex'], g['FEE'], g['last_close'], g['stats'], g['ms'], g['day']


def year_end_close(s, y, i_limit):
    """Last close of share s in calendar year y, using only days up to index i_limit."""
    d = S[s]; best = None
    for k in range(i_limit, -1, -1):
        t = CAL[k]
        if day(t).year < y:
            break
        if day(t).year == y and t in d:
            return d[t][1]
    return best


def quality_pick(i, n):
    t_now = CAL[i]; y_now = day(t_now).year
    cands = []
    for s, d in S.items():
        hist = [t for t in d if t <= t_now]
        if len(hist) < 5 * 240:
            continue
        cands.append((sum(d[t][1] * d[t][2] for t in hist if t > t_now - 365 * 86_400_000), s))
    uni = [s for _, s in sorted(cands, reverse=True)[:100]]
    feats = {}
    for s in uni:
        d = S[s]
        c_now = last_close(s, i)
        k5 = max(0, i - 5 * 245)
        c5 = last_close(s, k5)
        if not c_now or not c5:
            continue
        cagr5 = (c_now / c5) ** (1 / 5) - 1
        ends = [year_end_close(s, y, i) for y in range(y_now - 6, y_now)]
        ups = sum(1 for a, b in zip(ends, ends[1:]) if a and b and b > a)
        pk, dd = 0.0, 0.0
        for k in range(max(0, i - 3 * 245), i + 1):
            if CAL[k] in d:
                x = d[CAL[k]][1]; pk = max(pk, x); dd = min(dd, x / pk - 1)
        feats[s] = (cagr5, ups, dd)
    names = list(feats)
    rank = collections.Counter()
    for j, rev in ((0, True), (1, True), (2, True)):            # higher CAGR, more up years, shallower drop (dd closer to 0)
        for r, s in enumerate(sorted(names, key=lambda s: feats[s][j], reverse=rev)):
            rank[s] += r
    return sorted(names, key=lambda s: rank[s])[:n]


HELD = collections.Counter()


def backtest(n, start, end, months=(1,), fixed=None):
    i0 = next(k for k, t in enumerate(CAL) if t >= start)
    i1 = len(CAL) if end is None else next(k for k, t in enumerate(CAL) if t >= end)
    rebal = {k for k in range(i0, i1) if k == i0 or (day(CAL[k]).month != day(CAL[k - 1]).month and day(CAL[k]).month in months)}
    cash, hold, curve = 10000.0, {}, []
    for k in range(i0, i1):
        t = CAL[k]
        if k in rebal:
            want = [s for s in fixed if s in S and last_close(s, k - 1)] if fixed else quality_pick(k - 1, n)
            if not fixed:
                HELD.update(want)
            px = {s: (S[s][t][0] if t in S[s] and S[s][t][0] > 0 else last_close(s, k - 1)) for s in set(hold) | set(want)}
            value = cash + sum(q * px[s] for s, q in hold.items() if px[s])
            target = {s: value / len(want) for s in want if px[s]} if want else {}
            for s in list(hold):
                cur, tgt = hold[s] * px[s], target.get(s, 0.0)
                if cur > tgt:
                    cash += (cur - tgt) * (1 - FEE); hold[s] -= (cur - tgt) / px[s]
                    if hold[s] * px[s] < 1:
                        del hold[s]
            for s, tgt in target.items():
                cur = hold.get(s, 0.0) * px[s]
                if tgt > cur:
                    buy = min(tgt - cur, cash / (1 + FEE)); cash -= buy * (1 + FEE); hold[s] = hold.get(s, 0.0) + buy / px[s]
        curve.append((t, cash + sum(q * (last_close(s, k) or 0.0) for s, q in hold.items())))
    return curve


HALVES = [("2013-10..2019", ms(2013, 10, 1), ms(2020, 1, 1)), ("2020..2026-01", ms(2020, 1, 1), None)]
OWNER = ["BRACBANK", "UTTARABANK", "KOHINOOR", "SQURPHARMA", "MARICO", "IBNSINA"]
CASES = [("PRIMARY quality top 10, yearly", dict(n=10)), ("quality top 5, yearly", dict(n=5)),
         ("quality top 20, yearly", dict(n=20)), ("quality top 10, every 6 months", dict(n=10, months=(1, 7)))]
res = {}
L = ["Quality screen on DSE (5y growth + consistent up years + shallow 3y drop), top-100 liquid, 0.7%/side, price + bonus\n",
     f"{'strategy':36s} | " + " | ".join(f"{h:^28s}" for h, _, _ in HALVES)]
for name, c in CASES:
    row = f"{name:36s} |"
    for h, s, e in HALVES:
        m = stats(backtest(c['n'], s, e, c.get('months', (1,)))); res[(name, h)] = m
        row += f" {m['cagr']:+7.1%}  Sh {m['sharpe']:5.2f}  DD {m['dd']:6.1%} |"
    L.append(row)
row = f"{'owner six, equal weight (HINDSIGHT)':36s} |"
for h, s, e in HALVES:
    m = stats(backtest(6, s, e, (1,), fixed=OWNER)); row += f" {m['cagr']:+7.1%}  Sh {m['sharpe']:5.2f}  DD {m['dd']:6.1%} |"
L.append(row)
row = f"{'hold DSEX (price index)':36s} |"
for h, s, e in HALVES:
    m = stats([(t, dsex[t][1]) for t in CAL if t >= s and (e is None or t < e)]); res[("DSEX", h)] = m
    row += f" {m['cagr']:+7.1%}  Sh {m['sharpe']:5.2f}  DD {m['dd']:6.1%} |"
L.append(row)
P = CASES[0][0]
checks = [(f"beats DSEX, {h}", res[(P, h)]['cagr'] > res[("DSEX", h)]['cagr']) for h, _, _ in HALVES]
checks += [(f"worst drop within 5 pts of DSEX, {h}", res[(P, h)]['dd'] >= res[("DSEX", h)]['dd'] - 0.05) for h, _, _ in HALVES]
L += [""] + [f"  {'PASS' if ok else 'FAIL'}  {t}" for t, ok in checks]
L.append(f"verdict: {'PASS' if all(ok for _, ok in checks) else 'FAIL'}")
L.append("\nshares the screen held most often (all runs): " + ", ".join(f"{s} x{c}" for s, c in HELD.most_common(15)))
print("\n".join(L))
