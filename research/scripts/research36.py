"""Research round 36: 500 USDT for 5 years with today's set-ups. What CAGR?

The owner asked: "Under existing conditions, if I invest $500 for 5 years,
what will be the CAGR?" Round 25 answered for the old set-up (5 x 1%,
5 checks). This repeats it for what runs now:
  steady  8 slots x 0.5% risk, 6 of 8 checks (OKX demo; planned for real money)
  growth  8 slots x 1% risk, 6 of 8 checks (VPS testnet)
each with and without auto savings (idle USDT earning 3%/yr, round 32).

Method (decided before running, as in round 25):
  - Daily returns from round 21's six close-time versions, 2018-03 .. 2026-10,
    round 12's simulator, costs included, top 15.
  - Block bootstrap: 4,000 five-year paths of random 30-day blocks.
  - Scenarios: backtest (as is); realistic = minus a drag for live fills,
    latency and the survivorship/hindsight haircuts, 6%/yr at 1% risk as in
    round 25, scaled with the risk setting (3%/yr for steady); stress = only
    half of the daily excess return kept.
  - Output: CAGR percentiles (bad 5%, 25%, median, 75%, good 5%), final
    balance from 500, chance of ending below 500, the worst drop on the way.
  - Two pools of history: all of 2018-03 .. 2026-10, which includes the
    2020-21 bull market, and 2022-26 only, the more cautious view (bear
    market, chop and a recovery, closer to how crypto has behaved lately).
No pass bar: this is a planning model, not a rule test.
"""
import os as _os
import pickle
import random
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r36'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
old = "        curve.append((t, eq_of(t)))\n"
assert head.count(old) == 1
head = head.replace(old, "        cash *= (1 + YIELD) ** (1 / 365)\n        curve.append((t, eq_of(t)))\n")


def simulate(data):
    pk = _os.path.join(ROOT, 'research', 'data', '_r36_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r36b', 'YIELD': 0.0}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
CASES = [("steady", 0.005, 0.0), ("steady + savings 3%", 0.005, 0.03), ("growth", 0.01, 0.0), ("growth + savings 3%", 0.01, 0.03)]
series = {(c[0], pool): [] for c in CASES for pool in ("all", "recent")}
for o in OFFSETS:
    ns = simulate(unpack(raw[o]))
    for name, risk, y in CASES:
        ns['YIELD'] = y
        for pool, st in (("all", START), ("recent", SPLIT)):
            curve, _ = ns['run'](make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=risk, start=st + o * H)
            eq = [e for _, e in curve]
            series[(name, pool)].append([eq[i] / eq[i - 1] - 1 for i in range(1, len(eq))])

BLOCK, PATHS, DAYS, CAP = 30, 4000, 5 * 365, 500.0


def paths(src, scenario, risk, seed):
    rng = random.Random(seed)
    drag = 0.06 * (risk / 0.01) / 365
    out = []
    for _ in range(PATHS):
        eq, peak, dd, n = CAP, CAP, 0.0, 0
        while n < DAYS:
            r = src[rng.randrange(len(src))]; i = rng.randrange(0, len(r) - BLOCK)
            for x in r[i:i + BLOCK]:
                if scenario == "realistic":
                    x -= drag
                elif scenario == "stress":
                    x *= 0.5
                eq *= 1 + x; peak = max(peak, eq); dd = min(dd, eq / peak - 1); n += 1
                if n >= DAYS:
                    break
        out.append((eq, dd))
    return out


pc = lambda xs, q: sorted(xs)[min(len(xs) - 1, int(q * len(xs)))]
L = []
HDR = (f"{'set-up':22s} {'scenario':10s} | {'CAGR: bad 5%':>12s} {'25%':>7s} {'median':>7s} {'75%':>7s} {'good 5%':>8s} | "
     f"{'500 becomes (median)':>20s} {'bad 5%':>7s} {'good 5%':>8s} | {'P(<500)':>7s} {'typical worst drop':>18s}")
for pool, title in (("all", "history 2018-03 .. 2026-10 (includes the 2020-21 bull market)"), ("recent", "history 2022-01 .. 2026-10 only (the cautious view)")):
  L += [f"500 USDT for 5 years; 4,000 bootstrap paths of 30-day blocks, six close times, costs included; {title}\n", HDR]
  for k, (name, risk, _) in enumerate(CASES):
    for j, sc in enumerate(("backtest", "realistic", "stress")):
        res = paths(series[(name, pool)], sc, risk, seed=36 + 10 * k + j)
        fin = [e for e, _ in res]; dds = [d for _, d in res]
        cagr = [(e / CAP) ** (1 / 5) - 1 for e in fin]
        L.append(f"{name:22s} {sc:10s} | {pc(cagr, .05):+12.1%} {pc(cagr, .25):+7.1%} {pc(cagr, .5):+7.1%} {pc(cagr, .75):+7.1%} {pc(cagr, .95):+8.1%} | "
                 f"{pc(fin, .5):20,.0f} {pc(fin, .05):7,.0f} {pc(fin, .95):8,.0f} | {sum(e < CAP for e in fin) / len(fin):7.0%} {pc(dds, .5):18.0%}")
    L.append("")
print("\n".join(L))
