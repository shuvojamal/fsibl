"""Research round 55: are the indicator lengths a fragile sweet spot?

The checks use EMAs of 20 / 50 / 200 days, a 14-day ATR and a 20-day
breakout, chosen early on and never perturbed on the current set-up (8
slots, 6 of 8 checks). A real edge should degrade gently when they move a
little; a sharp drop would mean the backtest found a lucky combination.

Cases: live, and one parameter at a time moved about 25% down and up:
fast EMA 15/25, slow EMA 40/60, trend EMA 150/250, ATR 10/20, breakout
15/25 days (10 variants). Steady set-up (8 x 0.5%), top 15, round 12's
simulator and costs, round 21's six close times x two halves.

Pass bar (robustness, decided before running): the rules count as robust
if every variant's 2022-26 median return is within 4 points of live and its
median Sharpe within 0.15. Separately, a variant is only worth recommending
if it beats live's Sharpe in at least 9 of 12 cells AND adds at least 0.5
points of 2022-26 return or 1 point of shallower drop (effect-size floor).
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r55'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
CASES = [("live (20/50/200, ATR14, BO20)", {})]
for k, lo, hi in (("fast", 15, 25), ("slow", 40, 60), ("trend", 150, 250), ("atr_period", 10, 20), ("breakout", 15, 25)):
    CASES += [(f"{k} {lo}", {k: lo}), (f"{k} {hi}", {k: hi})]
res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for name, kw in CASES:
            res[(o, half, name)] = metrics(*run(make=lambda kw=kw: Opportunity(OppParams(min_score=6, **kw)), max_open=8, risk=0.005, start=s, end=e))

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
REF = CASES[0][0]
rb = med([res[(o, "2022-26", REF)]['cagr'] for o in OFFSETS]); rs = med([res[(o, "2022-26", REF)]['sharpe'] for o in OFFSETS])
rd = med([res[(o, "2022-26", REF)]['dd'] for o in OFFSETS])
L = ["Indicator lengths moved ~25% one at a time; steady 8 x 0.5%, 6 checks, top 15; medians over six close times\n",
     f"{'variant':30s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s} {'wins vs live':>13s} {'robust?':>8s} recommend?"]
robust = True
for name, _ in CASES:
    a = [res[(o, "2018-21", name)] for o in OFFSETS]; b = [res[(o, "2022-26", name)] for o in OFFSETS]
    ret, sh, dd = med([m['cagr'] for m in b]), med([m['sharpe'] for m in b]), med([m['dd'] for m in b])
    w = sum(res[(o, h, name)]['sharpe'] > res[(o, h, REF)]['sharpe'] for o, h in cells)
    rob = abs(ret - rb) <= 0.04 and abs(sh - rs) <= 0.15
    robust = robust and rob
    rec = name != REF and w >= 9 and (ret >= rb + 0.005 or dd >= rd + 0.01)
    L.append(f"{name:30s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} {ret:+8.1%} / {sh:4.2f} {dd:9.1%} "
             f"{'' if name == REF else f'{w} of 12':>13s} {'' if name == REF else ('yes' if rob else 'NO'):>8s} {'' if name == REF else ('YES' if rec else 'no')}")
L.append(f"\nverdict: {'ROBUST: results change gently when the lengths move' if robust else 'FRAGILE: at least one nearby setting changes results sharply'}")
print("\n".join(L))
