"""Research round 24: is "6 of 8 checks" really better than the live "5 of 8"?

Round 16 showed min_score=6 with the best Sharpe of 16 variants (1.25 vs the
live 0.97), but it was left alone because the best of many variants is
expected to look good by luck. This round tests it out of sample in a way
that selection can't explain: round 21's six versions of the data (daily
candles closing at 00, 04, 08, 12, 16 and 20 UTC) are six re-runs of
history that share the market but not the exact candles, and each is
split into 2018-21 and 2022-26. That gives 12 cells.

Pass bar, decided before running: min_score=6 replaces 5 only if it has the
higher Sharpe in at least 10 of the 12 cells AND does not lower the return
in the 00:00 / 2022-26 cell (the live set-up, most recent half). 4 and 7
are shown for context. Same simulator, universe, costs and caveats as
rounds 12 and 21.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r24'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SCORES = (4, 5, 6, 7)

res = {}   # (offset, half, score) -> metrics
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sc in SCORES:
            curve, trades = run(make=lambda sc=sc: Opportunity(OppParams(min_score=sc)), start=s, end=e)
            res[(o, half, sc)] = metrics(curve, trades)

L = ["min_score 4 / 5 (live) / 6 / 7 on six close times x two halves (30 coins, costs included)\n"]
L.append(f"{'close':6s} {'half':8s} " + "".join(f"{f'score {sc}: ret Sh trades':>32s}" for sc in SCORES))
for o in OFFSETS:
    for half in ("2018-21", "2022-26"):
        L.append(f"{o:02d}:00  {half:8s} " + "".join(
            f"{res[(o, half, sc)]['cagr']:+9.1%} {res[(o, half, sc)]['sharpe']:5.2f} {res[(o, half, sc)]['n']:5d}      " for sc in SCORES))
cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
for sc in (4, 6, 7):
    wins = sum(res[(o, h, sc)]['sharpe'] > res[(o, h, 5)]['sharpe'] for o, h in cells)
    d_ret = [res[(o, h, sc)]['cagr'] - res[(o, h, 5)]['cagr'] for o, h in cells]
    L.append(f"\nscore {sc} vs 5: higher Sharpe in {wins} of 12 cells; return difference median "
             f"{sorted(d_ret)[6]:+.1%}, range {min(d_ret):+.1%} to {max(d_ret):+.1%}")
w6 = sum(res[(o, h, 6)]['sharpe'] > res[(o, h, 5)]['sharpe'] for o, h in cells)
live_cell = res[(0, "2022-26", 6)]['cagr'] >= res[(0, "2022-26", 5)]['cagr']
L.append(f"\nPASS BAR for 6: >=10 of 12 Sharpe wins ({w6}) and no lower return at 00:00 2022-26 ({live_cell}) -> "
         f"{'PASS' if w6 >= 10 and live_cell else 'FAIL'}")
print("\n".join(L))
