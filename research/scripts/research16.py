"""Research round 16: deflated Sharpe ratio for the live strategy (idea from martex-dev/martex-quant).

Over 15 rounds this project tried hundreds of variants and kept the best.
The best of many random strategies has a high Sharpe by luck alone, so the
live strategy's backtest Sharpe has to clear that luck bar, not zero. The
deflated Sharpe ratio (Bailey & Lopez de Prado, 2014) is the probability that
the true Sharpe is above zero after accounting for:
  - the number of trials N (how many variants were looked at),
  - the spread of Sharpe across those trials,
  - the length of the sample, and non-normal returns (skew, fat tails).

Inputs: the live rules' daily returns 2017-2026 (round 12's simulator), and
the Sharpe of the variants round 12 ran (risk, universe, costs, ADX) as the
estimate of the trial-to-trial spread. N is uncertain, so it is swept.
Rough count of variants looked at across rounds 0-15: about 300.
"""
import math
import os as _os
from statistics import NormalDist

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research12.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r12'}
exec(src[:src.index('\nL = []')], ns)
run, metrics, Opportunity, OppParams, ADX = ns['run'], ns['metrics'], ns['Opportunity'], ns['OppParams'], ns['ADXFiltered']
FEE, SLIP = ns['FEE'], ns['SLIPPAGE']
Z = NormalDist()


def daily(curve):
    eq = [e for _, e in curve]
    return [eq[i] / eq[i - 1] - 1 for i in range(1, len(eq))]


def moments(r):
    n = len(r); mu = sum(r) / n
    sd = math.sqrt(sum((x - mu) ** 2 for x in r) / n)
    skew = sum((x - mu) ** 3 for x in r) / n / sd ** 3
    kurt = sum((x - mu) ** 4 for x in r) / n / sd ** 4
    return mu / sd, skew, kurt, n


def expected_max_sr(var_sr, n_trials):
    g = 0.5772156649
    return math.sqrt(var_sr) * ((1 - g) * Z.inv_cdf(1 - 1 / n_trials) + g * Z.inv_cdf(1 - 1 / (n_trials * math.e)))


def psr(sr, sr0, skew, kurt, n):
    return Z.cdf((sr - sr0) * math.sqrt(n - 1) / math.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr ** 2))


L = []
curve, trades = run()
r = daily(curve)
sr, skew, kurt, n = moments(r)
L.append(f"Live rules 2017-08 -> 2026-10: daily Sharpe {sr:.4f} (annualised {sr * math.sqrt(365):.2f}), "
         f"skew {skew:+.2f}, kurtosis {kurt:.1f}, {n} days")
L.append(f"Probability true Sharpe > 0 with NO trial correction (PSR): {psr(sr, 0, skew, kurt, n):.4f}")

variants = {
    "live rules": lambda: run(),
    "costs x2": lambda: run(fee=FEE * 2, slip=SLIP * 2),
    "costs x3": lambda: run(fee=FEE * 3, slip=SLIP * 3),
    "risk 0.5%": lambda: run(risk=0.005),
    "risk 2%": lambda: run(risk=0.02),
    "top 10": lambda: run(top=10),
    "top 20": lambda: run(top=20),
    "max open 3": lambda: run(max_open=3),
    "max open 8": lambda: run(max_open=8),
    "ADX>20": lambda: run(make=lambda: ADX(OppParams(), 20)),
    "ADX>25": lambda: run(make=lambda: ADX(OppParams(), 25)),
    "min score 4": lambda: run(make=lambda: Opportunity(OppParams(min_score=4))),
    "min score 6": lambda: run(make=lambda: Opportunity(OppParams(min_score=6))),
    "trail 2 ATR": lambda: run(make=lambda: Opportunity(OppParams(trail_atr=2.0))),
    "trail 4 ATR": lambda: run(make=lambda: Opportunity(OppParams(trail_atr=4.0))),
    "fixed 3:1 target, no trail": lambda: run(make=lambda: Opportunity(OppParams(trail_atr=0))),
}
srs = {}
L.append("\nVariant Sharpes (daily, used to estimate the spread across trials):")
for name, f in variants.items():
    s = moments(daily(f()[0]))[0]
    srs[name] = s
    L.append(f"  {name:28s} {s:.4f}  (annualised {s * math.sqrt(365):.2f})")
vals = list(srs.values()); m = sum(vals) / len(vals)
var_sr = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
L.append(f"variance of daily Sharpe across variants: {var_sr:.2e} (sd {math.sqrt(var_sr) * math.sqrt(365):.2f} annualised)")
# Variants of one family are similar; across the whole project (hourly bars, arbitrage, rotation...)
# the spread was much larger. Show both.
L.append("\nDeflated Sharpe ratio (probability the live rules' true Sharpe beats the best-of-N luck bar):")
L.append("   N trials | luck bar (annualised)  DSR, spread from variants | luck bar  DSR, spread x4 (whole-project)")
for N in (10, 50, 100, 300, 1000):
    b1 = expected_max_sr(var_sr, N); b2 = expected_max_sr(var_sr * 4, N)
    L.append(f"   {N:8d} | {b1 * math.sqrt(365):5.2f}  {psr(sr, b1, skew, kurt, n):.3f}"
             f"                     | {b2 * math.sqrt(365):5.2f}  {psr(sr, b2, skew, kurt, n):.3f}")
L.append("\nRule of thumb: DSR >= 0.95 is strong evidence; 0.5 means a coin flip between real edge and luck.")
print("\n".join(L))
