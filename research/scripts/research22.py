"""Research round 22: tranching across candle close times.

Round 21 found the same rules make +13% to +25% a year depending only on
which UTC hour the daily candle closes, with the live 00:00 close the best
of six. A standard fix for timing luck is tranching: split the capital into
equal sub-books that each run the identical rules on a different close
time, so no single hour decides the result.

Uses round 21's cached daily candles (research/data/daily_offsets.pkl.gz)
and round 12's simulator through round 21's helpers. Each tranche is
simulated separately (own 5 slots, 1% risk of its own capital), and the
books are combined with equal weight, rebalanced daily. Compared: 00:00
alone (live), the median single close time, and 2-, 3- and 6-tranche mixes.
Split check 2018-21 / 2022-26.
"""
import math
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r22'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H, DAY = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H'], ns['DAY']
START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

daily = {}        # offset -> {day index: equity at that day's close}
ntrades = {}
for o in OFFSETS:
    run, _ = simulate(unpack(raw[o]))
    curve, trades = run(start=START + o * H)
    daily[o] = {t // DAY: e for t, e in curve}
    ntrades[o] = len(trades)
days = sorted(set.intersection(*[set(v) for v in daily.values()]))


def combo(offs, lo=None, hi=None):
    ds = [x for x in days if (lo is None or x * DAY >= lo) and (hi is None or x * DAY < hi)]
    eq, cv = 1.0, [1.0]
    for a, b in zip(ds, ds[1:]):
        eq *= 1 + sum(daily[o][b] / daily[o][a] - 1 for o in offs) / len(offs)
        cv.append(eq)
    rets = [cv[i] / cv[i - 1] - 1 for i in range(1, len(cv))]
    pk = dd = 0
    for e in cv:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    mu = sum(rets) / len(rets); sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / len(rets))
    worst_year = min(cv[min(i + 365, len(cv) - 1)] / cv[i] - 1 for i in range(0, max(1, len(cv) - 365), 7))
    return cv[-1] ** (365 / len(cv)) - 1, dd, mu / sd * math.sqrt(365), worst_year


L = [f"{len(days)} common days, scored from 2018-03\n",
     f"{'book':36s} {'ret/yr':>8s} {'maxDD':>8s} {'Sharpe':>7s} {'worst 12m':>10s}   2018-21 ret/Sh     2022-26 ret/Sh"]
singles = {o: combo([o]) for o in OFFSETS}
med = sorted(OFFSETS, key=lambda o: singles[o][0])[len(OFFSETS) // 2]
books = [("00:00 alone (LIVE)", [0]), (f"median single ({med:02d}:00)", [med]),
         ("2 tranches: 00 + 12", [0, 12]), ("3 tranches: 00 + 08 + 16", [0, 8, 16]),
         ("3 tranches: 04 + 12 + 20 (no 00:00)", [4, 12, 20]), ("6 tranches: all", list(OFFSETS))]
for name, offs in books:
    c, dd, sh, wy = combo(offs)
    a = combo(offs, hi=SPLIT); b = combo(offs, lo=SPLIT)
    L.append(f"{name:36s} {c:+8.1%} {dd:8.1%} {sh:7.2f} {wy:+10.1%}   {a[0]:+7.1%} / {a[2]:.2f}    {b[0]:+7.1%} / {b[2]:.2f}")
L.append("\nsingle close times for reference: " + ", ".join(f"{o:02d}:00 {singles[o][0]:+.1%} (DD {singles[o][1]:.0%})" for o in OFFSETS))
L.append(f"trades per tranche over the period: {', '.join(f'{o:02d}:00 {ntrades[o]}' for o in OFFSETS)}")
print("\n".join(L))
