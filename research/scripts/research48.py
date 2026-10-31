"""Research round 48: how normal are losing streaks? (expectations before real money)

The VPS testnet closed its first three trades all at a loss (BNB, BTC, TRX,
2026-10-30/31, together -156.59 USDT, about -3% of 5,000). With a win rate
near 35% this is expected to happen often, but the owner should know how
often, how long streaks get, and how deep the account goes during them, so a
streak alone doesn't prompt switching the bot off at the wrong moment.

Method: trade sequences (in time order of exit) from round 12's simulator,
steady (8 x 0.5%) and growth (8 x 1%), 6 of 8 checks, top 15, on round 21's
six close times, 2018-03 .. 2026-10. Reported: win rate, longest losing
streak per run, how often a streak of 3 / 5 / 8+ losers happens per year,
the chance that a new account's first 3 trades are all losers, and what the
account had lost by the end of its worst streak.

Pass bar (an expectation test, decided before running): three losers in a
row counts as "normal, no action" if streaks of 3+ occur at least 3 times a
year on median AND an account's first three trades are all losers in at
least 15% of random starting days.
"""
import os as _os
import random
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r48'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
rng = random.Random(48)
out = {s: [] for s, _ in SETUPS}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for sname, r in SETUPS:
        curve, trades = run(make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r, start=START + o * H)
        out[sname].append((curve, sorted(trades, key=lambda x: x['t'])))

med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Losing streaks, whole period 2018-03 .. 2026-10, six close times\n"]
verdict = {}
for sname, r in SETUPS:
    longest, per_year3, per_year5, per_year8, wins, first3, worst_dd = [], [], [], [], [], [], []
    for curve, trades in out[sname]:
        years = (curve[-1][0] - curve[0][0]) / (365.25 * 86_400_000)
        wins.append(sum(x['pnl'] > 0 for x in trades) / len(trades))
        streaks, cur, run_loss, worst = [], 0, 0.0, 0.0
        eq_at = dict(curve)
        for x in trades:
            if x['pnl'] <= 0:
                cur += 1; run_loss += x['pnl']
            else:
                if cur: streaks.append((cur, run_loss))
                cur, run_loss = 0, 0.0
        if cur: streaks.append((cur, run_loss))
        longest.append(max(n for n, _ in streaks))
        per_year3.append(sum(n >= 3 for n, _ in streaks) / years)
        per_year5.append(sum(n >= 5 for n, _ in streaks) / years)
        per_year8.append(sum(n >= 8 for n, _ in streaks) / years)
        eq_med = sorted(e for _, e in curve)[len(curve) // 2]
        worst_dd.append(min(l for _, l in streaks) / eq_med)
        # chance a new account's first three trades all lose: start on random days
        ts = [x['t'] for x in trades]
        hits = 0
        for _ in range(2000):
            t0 = rng.choice(curve)[0]
            nxt = [x for x in trades if x['t'] >= t0][:3]
            hits += len(nxt) == 3 and all(x['pnl'] <= 0 for x in nxt)
        first3.append(hits / 2000)
    verdict[sname] = med(per_year3) >= 3 and med(first3) >= 0.15
    L += [sname,
          f"  win rate {med(wins):.0%} (median of six)",
          f"  longest losing streak per run: median {med(longest)}, worst {max(longest)}",
          f"  streaks of 3+ losers per year: median {med(per_year3):.1f}; 5+: {med(per_year5):.1f}; 8+: {med(per_year8):.2f}",
          f"  chance a new account's first 3 trades all lose: median {med(first3):.0%} (range {min(first3):.0%}-{max(first3):.0%})",
          f"  worst single streak's total loss: median {med(worst_dd):.1%} of typical equity, worst {min(worst_dd):.1%}",
          f"  -> three losers in a row is {'NORMAL (no action)' if verdict[sname] else 'not as common as assumed'}", ""]
print("\n".join(L))
