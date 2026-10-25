"""Research round 37: can the bot make 30% a year for 5 years? How likely, at what risk?

The owner asked whether a 30% CAGR over 5 years is possible in any way.
Same model as round 36 (4,000 five-year block-bootstrap paths from round
21's six close times, costs included, realistic drag scaled with risk:
6%/yr at 1% risk), on both history pools (2018-26 and the cautious 2022-26).
Cases: steady 0.5%, growth 1%, and two riskier settings the app allows,
1.5% and 2% risk per trade, all 8 slots, 6 of 8 checks, auto savings at 3%.
Reported: chance of a 5-year CAGR of at least 30%, the median CAGR, the
chance of ending below the starting money, and the typical and bad-case
(1 in 20) worst drop along the way.
No pass bar: a planning question, not a rule test.
"""
import os as _os
import pickle
import random
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r37'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
old = "        curve.append((t, eq_of(t)))\n"
assert head.count(old) == 1
head = head.replace(old, "        cash *= (1 + YIELD) ** (1 / 365)\n        curve.append((t, eq_of(t)))\n")


def simulate(data):
    pk = _os.path.join(ROOT, 'research', 'data', '_r37_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r37b', 'YIELD': 0.0}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
CASES = [("steady 0.5%", 0.005), ("growth 1%", 0.01), ("risk 1.5%", 0.015), ("risk 2%", 0.02)]
series = {(c[0], pool): [] for c in CASES for pool in ("all", "recent")}
for o in OFFSETS:
    ns = simulate(unpack(raw[o]))
    ns['YIELD'] = 0.03
    for name, risk in CASES:
        for pool, st in (("all", START), ("recent", SPLIT)):
            curve, _ = ns['run'](make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=risk, start=st + o * H)
            eq = [e for _, e in curve]
            series[(name, pool)].append([eq[i] / eq[i - 1] - 1 for i in range(1, len(eq))])

BLOCK, PATHS, DAYS, CAP = 30, 4000, 5 * 365, 500.0


def paths(src, risk, seed):
    rng = random.Random(seed)
    drag = 0.06 * (risk / 0.01) / 365
    out = []
    for _ in range(PATHS):
        eq, peak, dd, n = CAP, CAP, 0.0, 0
        while n < DAYS:
            r = src[rng.randrange(len(src))]; i = rng.randrange(0, len(r) - BLOCK)
            for x in r[i:i + BLOCK]:
                eq *= 1 + x - drag; peak = max(peak, eq); dd = min(dd, eq / peak - 1); n += 1
                if n >= DAYS:
                    break
        out.append((eq, dd))
    return out


pc = lambda xs, q: sorted(xs)[min(len(xs) - 1, int(q * len(xs)))]
L = ["Realistic scenario, auto savings 3%, 8 slots, 6 checks; 4,000 five-year paths\n"]
for pool, title in (("all", "history 2018-26 (with the 2020-21 bull market)"), ("recent", "history 2022-26 only (cautious)")):
    L += [title, f"  {'set-up':12s} {'P(CAGR>=30%)':>12s} {'median CAGR':>11s} {'P(loss)':>8s} {'typical worst drop':>18s} {'bad-case drop':>13s} {'500 -> median':>13s}"]
    for k, (name, risk) in enumerate(CASES):
        res = paths(series[(name, pool)], risk, seed=37 + k)
        fin = [e for e, _ in res]; dds = [d for _, d in res]
        cagr = [(e / CAP) ** (1 / 5) - 1 for e in fin]
        L.append(f"  {name:12s} {sum(c >= 0.30 for c in cagr) / len(cagr):12.0%} {pc(cagr, .5):+11.1%} {sum(e < CAP for e in fin) / len(fin):8.0%} "
                 f"{pc(dds, .5):18.0%} {pc(dds, .05):13.0%} {pc(fin, .5):13,.0f}")
    L.append("")
print("\n".join(L))
