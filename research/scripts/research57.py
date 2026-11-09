"""Research round 57: how much do fees and slippage matter for the real account?

Binance charges 0.10% per spot trade, or 0.075% when fees are paid in BNB
(a balance of BNB must be kept for that). Slippage on a 300-500 USDT
account's market orders in top-15 coins should be small, but grows in
fast markets. The backtests assume 0.10% fee + 0.05% slippage per side.

Grid: fee 0.075% / 0.10% / 0.15% x slippage 0.02% / 0.05% / 0.15% per side,
steady (8 x 0.5%) and growth (8 x 1%), 6 of 8 checks, top 15, round 12's
simulator, round 21's six close times x two halves.

Pass bar, decided before running: paying fees in BNB is "worth recommending"
if 0.075% adds at least 0.3 points a year to the 2022-26 median return over
0.10% (both at 0.05% slippage). Also reported: how much return each extra
0.05% of cost per side takes away (sensitivity).
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r57'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
FEES, SLIPS = (0.00075, 0.001, 0.0015), (0.0002, 0.0005, 0.0015)
res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sname, r in SETUPS:
            for fee in FEES:
                for slip in SLIPS:
                    res[(o, half, sname, fee, slip)] = metrics(*run(make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r,
                                                                     fee=fee, slip=slip, start=s, end=e))

med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Costs per side (fee x slippage); 2022-26 median yearly return (2018-21 in brackets); 8 slots, 6 checks, top 15\n"]
verdict = {}
for sname, _ in SETUPS:
    L += [sname, f"  {'fee \\ slippage':16s}" + "".join(f"{s:>20.2%}" for s in SLIPS)]
    for fee in FEES:
        row = f"  {fee:<16.3%}"
        for slip in SLIPS:
            b = med([res[(o, "2022-26", sname, fee, slip)]['cagr'] for o in OFFSETS])
            a = med([res[(o, "2018-21", sname, fee, slip)]['cagr'] for o in OFFSETS])
            row += f"{b:+11.1%} ({a:+5.1%})"
        L.append(row)
    bnb = med([res[(o, "2022-26", sname, 0.00075, 0.0005)]['cagr'] for o in OFFSETS])
    std = med([res[(o, "2022-26", sname, 0.001, 0.0005)]['cagr'] for o in OFFSETS])
    hi = med([res[(o, "2022-26", sname, 0.0015, 0.0005)]['cagr'] for o in OFFSETS])
    verdict[sname] = bnb - std >= 0.003
    L += [f"  BNB fee (0.075%) vs standard (0.10%): {100 * (bnb - std):+.1f} points a year -> {'worth it' if verdict[sname] else 'not worth the bother'}",
          f"  each extra 0.05% per side costs about {100 * (std - hi):.1f} points a year", ""]
print("\n".join(L))
