"""Research round 49: a coin collapses while held. What does a backstop order save?

The backtests can't contain a LUNA- or FTT-style collapse (dead coins were
delisted and are missing from the data, rounds 12/26), and the daily-close
stop can't react to a crash between closes. On OKX a resting backstop order
sits 20% below each stop; the Binance accounts have none (rounds 45-48
recommend adding one). This puts a number on it.

Stress test: for every position the live rules opened (round 12's simulator,
growth 8 x 1% and steady 8 x 0.5%, 6 of 8 checks, top 15, round 21's six
close times, 2018-03 .. 2026-10), assume that coin crashes 90% overnight
right after entry (worst case: nothing else moves, the trail hasn't risen).
  - no backstop: the daily stop sells after the crash, at -90%;
  - backstop 20% below the stop: fills on the way down, with 10% extra
    slippage on the fill in a crash.
Loss as a share of the account = position share x the loss on the coin.

Pass bar for calling a Binance backstop "high priority before real money",
decided before running: on the growth set-up, the 90th-percentile position
loses more than 5% of the account without a backstop AND the backstop at
least halves that loss.
"""
import os as _os
import pickle
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r49'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
a = "risk=qty * (entry - plan.stop), bull=btc_bull.get(t, False))"
assert a in head
head = head.replace(a, "risk=qty * (entry - plan.stop), bull=btc_bull.get(t, False))\n                ENTRIES.append((qty * entry / eq_now, plan.stop / entry))")


def simulate(data):
    pk = _os.path.join(ROOT, 'research', 'data', '_r49_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r49b', 'ENTRIES': []}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("growth 8 x 1%", 0.01), ("steady 8 x 0.5%", 0.005)]
CRASH, BACK, SLIP = 0.90, 0.20, 0.10
E = {s: [] for s, _ in SETUPS}
for o in OFFSETS:
    ns = simulate(unpack(raw[o]))
    for sname, r in SETUPS:
        ns['ENTRIES'].clear()
        ns['run'](make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r, start=START + o * H)
        E[sname] += list(ns['ENTRIES'])

pc = lambda xs, q: sorted(xs)[min(len(xs) - 1, int(q * len(xs)))]
L = [f"A coin collapses {CRASH:.0%} overnight right after entry: loss as a share of the account\n",
     f"{'set-up':16s} {'positions':>9s} | {'no backstop: median / 90th / worst':>36s} | {'backstop 20% below stop: median / 90th / worst':>48s}"]
verdict = None
for sname, r in SETUPS:
    no = [sh * CRASH for sh, _ in E[sname]]
    bs = [sh * min(CRASH, 1 - st * (1 - BACK) * (1 - SLIP)) for sh, st in E[sname]]
    L.append(f"{sname:16s} {len(no):9d} | {pc(no, .5):10.1%} {pc(no, .9):10.1%} {max(no):12.1%} | {pc(bs, .5):14.1%} {pc(bs, .9):14.1%} {max(bs):16.1%}")
    if sname.startswith("growth"):
        verdict = pc(no, .9) > 0.05 and pc(bs, .9) <= pc(no, .9) / 2
L.append("\nFor scale: the planned loss of a normal stop-out is 1% (growth) or 0.5% (steady) of the account.")
L.append(f"verdict: {'PASS: a Binance backstop is high priority before real money' if verdict else 'FAIL: backstop helps less than assumed'}")
print("\n".join(L))
