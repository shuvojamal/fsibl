"""Research round 30: bet bigger in bull markets? Regime-based risk per trade.

The owner wants more return than ~15%/yr. Round 28 showed that simply
risking more (8 x 1%) raises return but deepens the worst drop to ~-40%.
Most of the strategy's losses come in bear markets (2018, 2022, 2025), so:
risk more per trade only while BTC is above its 200-day EMA, less while
it's below. (Round 11 rejected a BTC filter on *entries*; this keeps every
entry and changes only the size.)

Cases, all with 8 slots and 6 of 8 checks (round 29's recommendation),
top-15 universe, on round 21's six close times x two halves:
  flat 0.5%                  (round 29's recommended set-up)
  flat 1%                    (round 28's "higher return" set-up)
  bull 1% / bear 0.5%
  bull 1.5% / bear 0.5%
  bull 1% / bear 0.25%

Pass bar, decided before running: a regime case is recommended over flat
1% if it has the higher Sharpe in at least 9 of 12 cells AND a 2022-26
median worst drop at least 5 points shallower, with a 2022-26 median return
no more than 2 points lower.
"""
import os as _os
import pickle
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r30'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
old = "qty = min(eq_now * risk / (entry - plan.stop), cash * (1 - fee) / entry)"
assert old in head
head = head.replace(old, "qty = min(eq_now * (RISK_BULL if btc_bull.get(t, False) else RISK_BEAR) / (entry - plan.stop), cash * (1 - fee) / entry)")


def simulate(data):
    pk = _os.path.join(ROOT, 'research', 'data', '_r30_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r30b', 'RISK_BULL': 0.01, 'RISK_BEAR': 0.01}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
CASES = [("flat 0.5%", 0.005, 0.005), ("flat 1% (reference)", 0.01, 0.01), ("bull 1% / bear 0.5%", 0.01, 0.005),
         ("bull 1.5% / bear 0.5%", 0.015, 0.005), ("bull 1% / bear 0.25%", 0.01, 0.0025)]
REF = "flat 1% (reference)"
make = lambda: Opportunity(OppParams(min_score=6))

res = {}
for o in OFFSETS:
    ns = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for name, rb, rs in CASES:
            ns['RISK_BULL'], ns['RISK_BEAR'] = rb, rs
            curve, trades = ns['run'](make=make, max_open=8, start=s, end=e)
            res[(o, half, name)] = ns['metrics'](curve, trades)

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
ref_b = [res[(o, "2022-26", REF)] for o in OFFSETS]
ref_dd, ref_ret = med([m['dd'] for m in ref_b]), med([m['cagr'] for m in ref_b])
L = ["Regime-based risk per trade (BTC above/below its 200-day EMA); 8 slots, 6 checks, top 15; medians over six close times\n",
     f"{'case':24s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 18-21':>9s} {'DD 22-26':>9s} {'wins vs flat 1%':>16s} verdict"]
for name, _, _ in CASES:
    a = [res[(o, "2018-21", name)] for o in OFFSETS]; b = [res[(o, "2022-26", name)] for o in OFFSETS]
    w = sum(res[(o, h, name)]['sharpe'] > res[(o, h, REF)]['sharpe'] for o, h in cells)
    dd, ret = med([m['dd'] for m in b]), med([m['cagr'] for m in b])
    ok = name.startswith("bull") and w >= 9 and dd >= ref_dd + 0.05 and ret >= ref_ret - 0.02
    L.append(f"{name:24s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} "
             f"{ret:+8.1%} / {med([m['sharpe'] for m in b]):4.2f} {med([m['dd'] for m in a]):9.1%} {dd:9.1%} "
             f"{'' if name == REF else f'{w} of 12':>16s} {'REF' if name == REF else ('PASS' if ok else '')}")
print("\n".join(L))
