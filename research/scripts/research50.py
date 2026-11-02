"""Research round 50: after 49 rounds, is the edge still more than luck? (deflated Sharpe, updated)

Round 16 checked the live rules against the "luck bar" (Bailey & Lopez de
Prado's deflated Sharpe ratio) assuming about 300 variants had been looked
at. Rounds 17-49 added many more (sizing grids, checks, exits, outages, DSE,
...), roughly 300 more, so about 600 in all. The current set-ups also differ
(8 slots, 6 of 8 checks). The more variants tried, the higher the best one
scores by luck, so the bar rises.

Method (round 16's, unchanged): daily returns of the current set-ups on round
12's 55-coin data, 2017-08 .. 2026-10; spread of Sharpe across trials
estimated from a grid of nearby variants (risk 0.5/1/1.5%, 5/8/10 slots,
5/6/7 checks, trail 2/3/4 x ATR), plus round 16's conservative "spread x4".
N swept 100 / 300 / 600 / 1000.

Pass bar, decided before running: the edge still counts as real if the
steady set-up's DSR is at least 0.95 at N = 600 with the variant spread.
(Below that, the strategy may still work, but the evidence is weaker than
claimed and the planning numbers should be treated more cautiously.)
"""
import math
import os as _os
from statistics import NormalDist

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research12.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r50'}
exec(src[:src.index('\nL = []')], ns)
run, Opportunity, OppParams = ns['run'], ns['Opportunity'], ns['OppParams']
Z = NormalDist()


def daily(curve):
    eq = [e for _, e in curve]
    return [eq[i] / eq[i - 1] - 1 for i in range(1, len(eq))]


def moments(r):
    n = len(r); mu = sum(r) / n
    sd = math.sqrt(sum((x - mu) ** 2 for x in r) / n)
    return mu / sd, sum((x - mu) ** 3 for x in r) / n / sd ** 3, sum((x - mu) ** 4 for x in r) / n / sd ** 4, n


def expected_max_sr(var_sr, n_trials):
    g = 0.5772156649
    return math.sqrt(var_sr) * ((1 - g) * Z.inv_cdf(1 - 1 / n_trials) + g * Z.inv_cdf(1 - 1 / (n_trials * math.e)))


def psr(sr, sr0, skew, kurt, n):
    return Z.cdf((sr - sr0) * math.sqrt(n - 1) / math.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr ** 2))


def sharpe_of(**kw):
    p = dict(min_score=kw.pop('ms', 6), trail_atr=kw.pop('trail', 3.0))
    return moments(daily(run(make=lambda: Opportunity(OppParams(**p)), **kw)[0]))[0]


grid = []
for risk in (0.005, 0.01, 0.015):
    for slots in (5, 8, 10):
        grid.append(sharpe_of(max_open=slots, risk=risk))
for ms in (5, 7):
    grid.append(sharpe_of(max_open=8, risk=0.005, ms=ms))
for tr in (2.0, 4.0):
    grid.append(sharpe_of(max_open=8, risk=0.005, trail=tr))
mu = sum(grid) / len(grid)
var = sum((x - mu) ** 2 for x in grid) / len(grid)

L = [f"Spread of daily Sharpe across {len(grid)} nearby variants: sd {math.sqrt(var) * math.sqrt(365):.2f} annualised\n"]
verdict = None
for name, risk in (("steady 8 x 0.5%, 6 checks", 0.005), ("growth 8 x 1%, 6 checks", 0.01)):
    sr, skew, kurt, n = moments(daily(run(make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=risk)[0]))
    L += [f"{name}: daily Sharpe {sr:.4f} (annualised {sr * math.sqrt(365):.2f}), skew {skew:+.2f}, kurtosis {kurt:.1f}, {n} days;"
          f" no-correction PSR {psr(sr, 0, skew, kurt, n):.4f}",
          f"  {'N trials':>9s} | {'luck bar':>8s} {'DSR (variant spread)':>21s} | {'luck bar':>8s} {'DSR (spread x4)':>16s}"]
    for N in (100, 300, 600, 1000):
        b1, b4 = expected_max_sr(var, N), expected_max_sr(var * 4, N)
        d1, d4 = psr(sr, b1, skew, kurt, n), psr(sr, b4, skew, kurt, n)
        L.append(f"  {N:9d} | {b1 * math.sqrt(365):8.2f} {d1:21.3f} | {b4 * math.sqrt(365):8.2f} {d4:16.3f}")
        if name.startswith("steady") and N == 600:
            verdict = d1 >= 0.95
    L.append("")
L.append(f"verdict: {'PASS: the edge still clears the luck bar at N = 600' if verdict else 'FAIL: evidence weaker than claimed at N = 600'}")
L.append("Rule of thumb: DSR >= 0.95 strong evidence; 0.5 = a coin flip between real edge and luck.")
print("\n".join(L))
