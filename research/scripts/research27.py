"""Research round 27: is the trailing stop good, and is 3 x ATR the right distance?

The owner asked whether the trailing stop is good. Round 16 showed the
3xATR trail ahead of a fixed 3:1 target (Sharpe 0.97 vs 0.74), on one data
set. Here the exit is tested the same way as round 24, on round 21's six
close-time versions x two halves (12 cells):
  - ATR trailing stop at 2, 2.5, 3 (live), 3.5, 4 and 5 x ATR
  - a plain percentage trailing stop: 10%, 15%, 20%, 25% below the highest
    close (what most trading apps offer)
  (A fixed 3:1 target was also planned, but round 12's simulator only
  exits on stops, so that variant can't be run fairly here; round 16
  already compared it: Sharpe 0.74 vs 0.97 for the trail.)
Entries, stops at entry (2xATR), sizing, universe and costs as in round 12.

Pass bar, decided before running: the live 3xATR trail is "fine" if no
other exit beats its Sharpe in at least 9 of the 12 cells. If one does, it
becomes a recommendation for the owner, not a change.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r27'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams


class PctTrail(Opportunity):
    """Trailing stop a fixed percentage below the highest close, instead of an ATR multiple."""
    def __init__(self, pct):
        super().__init__(OppParams())
        self.pct = pct

    def update_stop(self, i, stop):
        self.peak = max(self.peak or 0.0, self.closes[i])
        return max(stop, self.peak * (1 - self.pct))


EXITS = [(f"ATR x{a:g}" + (" (live)" if a == 3 else ""), (lambda a=a: Opportunity(OppParams(trail_atr=a)))) for a in (2, 2.5, 3, 3.5, 4, 5)]
EXITS += [(f"{p:.0%} below high", (lambda p=p: PctTrail(p))) for p in (0.10, 0.15, 0.20, 0.25)]
START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for name, make in EXITS:
            curve, trades = run(make=make, start=s, end=e)
            res[(o, half, name)] = metrics(curve, trades)

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
live = EXITS[2][0]
L = ["Exit rules on six close times x two halves (30 coins, costs included).",
     "Per half: median over the six close times (return/yr, Sharpe); then wins vs the live trail over all 12 cells.\n",
     f"{'exit':22s} {'2018-21 ret / Sh':>18s} {'2022-26 ret / Sh':>18s} {'DD 22-26':>9s} {'trades 22-26':>13s} {'wins vs live':>13s}"]
med = lambda xs: sorted(xs)[len(xs) // 2]
for name, _ in EXITS:
    a = [res[(o, "2018-21", name)] for o in OFFSETS]; b = [res[(o, "2022-26", name)] for o in OFFSETS]
    w = sum(res[(o, h, name)]['sharpe'] > res[(o, h, live)]['sharpe'] for o, h in cells)
    wb = sum(res[(o, "2022-26", name)]['sharpe'] > res[(o, "2022-26", live)]['sharpe'] for o in OFFSETS)
    L.append(f"{name:22s} {med([m['cagr'] for m in a]):+9.1%} / {med([m['sharpe'] for m in a]):4.2f}  {med([m['cagr'] for m in b]):+9.1%} / "
             f"{med([m['sharpe'] for m in b]):4.2f}  {med([m['dd'] for m in b]):8.1%} {med([m['n'] for m in b]):13d} "
             f"{'' if name == live else f'{w}/12 ({wb}/6 recent)':>13s}")
L += ["", "Median over all 12 cells (dominated by the 2018-21 bull market; read with the table above):",
     f"{'exit':28s} {'return/yr':>10s} {'Sharpe':>7s} {'max DD':>8s} {'trades':>7s} {'avg R':>6s} {'win':>5s} {'beats live (Sharpe)':>20s}"]
med = lambda xs: sorted(xs)[len(xs) // 2]
for name, _ in EXITS:
    ms = [res[(o, h, name)] for o, h in cells]
    beats = sum(res[(o, h, name)]['sharpe'] > res[(o, h, live)]['sharpe'] for o, h in cells)
    L.append(f"{name:28s} {med([m['cagr'] for m in ms]):+10.1%} {med([m['sharpe'] for m in ms]):7.2f} {med([m['dd'] for m in ms]):8.1%} "
             f"{med([m['n'] for m in ms]):7d} {med([m['exp_r'] for m in ms]):+6.2f} {med([m['win'] for m in ms]):5.0%} "
             f"{'' if name == live else f'{beats} of 12':>20s}")
best = max((n for n, _ in EXITS if n != live), key=lambda n: sum(res[(o, h, n)]['sharpe'] > res[(o, h, live)]['sharpe'] for o, h in cells))
bw = sum(res[(o, h, best)]['sharpe'] > res[(o, h, live)]['sharpe'] for o, h in cells)
L.append(f"\nstrongest challenger: {best}, beats the live trail in {bw} of 12 cells -> live trail "
         f"{'FINE (pass)' if bw < 9 else 'BEATEN (recommend a change to the owner)'}")
print("\n".join(L))
