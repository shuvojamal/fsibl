"""Research round 25: a financial model for the owner's own money.

The owner plans to start with 300-500 USDT. What range of outcomes should
they plan for over 1, 2, 3 and 5 years, and how likely is a loss?

Method (decided before running):
  - Daily returns of the live rules from round 21's six close-time versions
    of 2018-03 .. 2026-10 (30 coins, costs included). Pooling all six bakes
    the timing luck of round 21 into the model.
  - Block bootstrap: 4,000 paths built from random 30-day blocks of those
    daily returns (each block from a random close time and start date), so
    winning and losing streaks stay intact.
  - Three scenarios:
      backtest      the returns as they are
      realistic     minus 6%/yr (live fills, data/latency drag, the
                    survivorship and hindsight haircuts of rounds 12/16)
      stress        only half of the strategy's excess daily return kept
  - Benchmarks on the same days: buying BTC and holding it (block-
    bootstrapped the same way), and a 4%/yr savings rate.
  - Starting capital 300 USDT, plus a variant with 50 USDT added monthly.
Outputs: percentiles of the final balance, the chance of being below the
money put in, and the worst drawdown along the way.
"""
import math
import os as _os
import random
import statistics
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r25'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
series, btc = [], []
for o in OFFSETS:
    data = unpack(raw[o])
    run, _ = simulate(data)
    curve, _ = run(start=START + o * H)
    eq = [e for _, e in curve]
    series.append([eq[i] / eq[i - 1] - 1 for i in range(1, len(eq))])
    b = [c.close for c in data['BTCUSDT'] if c.open_time >= START + o * H]
    btc.append([b[i] / b[i - 1] - 1 for i in range(1, len(b))])

BLOCK, PATHS, SEED = 30, 4000, 25
rng = random.Random(SEED)
DRAG = 0.06 / 365


def draw_path(days, source, scenario):
    out = []
    while len(out) < days:
        s = rng.randrange(len(source)); r = source[s]
        i = rng.randrange(0, len(r) - BLOCK)
        for x in r[i:i + BLOCK]:
            if scenario == "realistic":
                x -= DRAG
            elif scenario == "stress":
                x *= 0.5
            out.append(x)
    return out[:days]


def simulate_money(scenario, start=300.0, monthly=0.0, source=None, horizons=(1, 2, 3, 5)):
    """One 5-year path per draw; balances read off at each horizon."""
    source = source or series
    marks = {int(365 * y): y for y in horizons}
    finals = {y: [] for y in horizons}; dds = {y: [] for y in horizons}; below = {y: 0 for y in horizons}
    for _ in range(PATHS):
        eq, put_in, peak, dd = start, start, start, 0.0
        for d, r in enumerate(draw_path(max(marks), source, scenario), 1):
            if monthly and d % 30 == 0:
                eq += monthly; put_in += monthly
            eq *= 1 + r
            peak = max(peak, eq); dd = min(dd, eq / peak - 1)
            if d in marks:
                y = marks[d]; finals[y].append(eq); dds[y].append(dd); below[y] += eq < put_in
    out = {}
    for y in horizons:
        f = sorted(finals[y]); dd_ = sorted(dds[y]); q = lambda a, x: a[int(x * (len(a) - 1))]
        out[y] = dict(p5=q(f, .05), p25=q(f, .25), p50=q(f, .5), p75=q(f, .75), p95=q(f, .95), loss=below[y] / PATHS,
                      dd_med=q(dd_, .5), dd_bad=q(dd_, .05), put_in=start + monthly * (int(365 * y) // 30))
    return out


ann = lambda r: (1 + statistics.mean(r)) ** 365 - 1
L = [f"Daily returns: {len(series)} close-time versions x ~{len(series[0])} days (2018-03 .. 2026-10), "
     f"avg {statistics.mean(ann(s) for s in series):+.1%}/yr arithmetic; {PATHS} paths of {BLOCK}-day blocks\n"]
for monthly in (0.0, 50.0):
    L.append(f"## Start 300 USDT{' + 50 USDT a month' if monthly else ''}")
    L.append(f"  {'scenario':10s} {'years':>5s} {'put in':>8s} {'bad 5%':>9s} {'25%':>9s} {'median':>9s} {'75%':>9s} {'good 5%':>9s} "
             f"{'P(below put-in)':>16s} {'typical worst drop':>19s} {'bad-case drop':>14s}")
    for scen in ("backtest", "realistic", "stress"):
        res = simulate_money(scen, monthly=monthly)
        for yrs, m in res.items():
            L.append(f"  {scen:10s} {yrs:5d} {m['put_in']:8.0f} {m['p5']:9.0f} {m['p25']:9.0f} {m['p50']:9.0f} {m['p75']:9.0f} "
                     f"{m['p95']:9.0f} {m['loss']:16.0%} {m['dd_med']:19.0%} {m['dd_bad']:14.0%}")
    res = simulate_money("backtest", monthly=monthly, source=btc, horizons=(1, 3, 5))
    for yrs, b in res.items():
        sav = 300 * 1.04 ** yrs + sum(monthly * 1.04 ** ((yrs * 365 - d) / 365) for d in range(30, yrs * 365 + 1, 30))
        L.append(f"  {'hold BTC':10s} {yrs:5d} {b['put_in']:8.0f} {b['p5']:9.0f} {b['p25']:9.0f} {b['p50']:9.0f} {b['p75']:9.0f} "
                 f"{b['p95']:9.0f} {b['loss']:16.0%} {b['dd_med']:19.0%} {b['dd_bad']:14.0%}   (savings at 4%: {sav:.0f})")
    L.append("")
print("\n".join(L))
