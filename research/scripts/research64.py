"""Research round 64: skip the most volatile coins by rule (a principled version of round 62)?

Round 62 found that leaving out DOGE, SHIB and PEPE added 1.5-2 points a
year in 2022-26, likely because their violent reversals stop the bot out.
A hand-picked list is fragile (who counts as a meme coin next year?). If
the mechanism is volatility, a rule should do the same: each quarter, when
the top 15 by volume is re-ranked, drop the N with the highest volatility
over the previous 90 days (daily return standard deviation), N = 2 or 3,
and fill from the next coins by volume.

Cases: live; drop the 2 / 3 most volatile; and round 62's named list for
comparison. Steady and growth, 6 of 8 checks, round 12's simulator and costs,
round 21's six close times x two halves.

Pass bar, decided before running (with round 53's effect-size floor): a rule
is recommended only if it has a higher Sharpe than live in at least 9 of 12
cells AND adds at least 0.5 points of 2022-26 median return or makes the
median worst drop at least 1 point shallower, on both set-ups.
"""
import math
import os as _os
import pickle
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r64'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
# re-rank: drop the DROP most volatile of the volume ranking (computed per quarter, no look-ahead)
a = "    rank_at[qs] = sorted((s for s in vols if vols[s] > 0), key=vols.get, reverse=True)\n"
assert head.count(a) == 1
head = head.replace(a, a + """    _vol = {}
    for s, cs in data.items():
        cl = [c.close for c in cs if qs - QUARTER <= c.open_time < qs]
        rr = [cl[k] / cl[k - 1] - 1 for k in range(1, len(cl))]
        if len(rr) > 30:
            m_ = sum(rr) / len(rr); _vol[s] = math.sqrt(sum((x - m_) ** 2 for x in rr) / len(rr))
    _top = rank_at[qs][:15 + 5]
    _wild = set(sorted((s for s in _top[:15] if s in _vol), key=_vol.get, reverse=True)[:DROP]) if DROP else set()
    rank_at[qs] = [s for s in rank_at[qs] if s not in _wild and s not in EXCLUDE]
""")


def simulate(data, drop, exclude):
    pk = _os.path.join(ROOT, 'research', 'data', '_r64_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r64b', 'DROP': drop, 'EXCLUDE': exclude, 'math': math}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


MEME = {"DOGEUSDT", "SHIBUSDT", "PEPEUSDT"}
START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
CASES = [("live", 0, set()), ("drop 2 most volatile", 2, set()), ("drop 3 most volatile", 3, set()), ("no meme coins (round 62)", 0, MEME)]
res = {}
for o in OFFSETS:
    data = unpack(raw[o])
    for cname, drop, ex in CASES:
        ns = simulate(data, drop, ex)
        for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
            for sname, r in SETUPS:
                res[(o, half, sname, cname)] = ns['metrics'](*ns['run'](make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r, start=s, end=e))

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Drop the most volatile coins from the top 15 each quarter; 8 slots, 6 checks; medians over six close times\n"]
ok_all = {c[0]: True for c in CASES[1:]}
for sname, _ in SETUPS:
    ref = CASES[0][0]
    rb = med([res[(o, "2022-26", sname, ref)]['cagr'] for o in OFFSETS]); rd = med([res[(o, "2022-26", sname, ref)]['dd'] for o in OFFSETS])
    L += [sname, f"  {'universe':26s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s} {'wins vs live':>13s} pass?"]
    for cname, _, _ in CASES:
        a = [res[(o, "2018-21", sname, cname)] for o in OFFSETS]; b = [res[(o, "2022-26", sname, cname)] for o in OFFSETS]
        w = sum(res[(o, h, sname, cname)]['sharpe'] > res[(o, h, sname, ref)]['sharpe'] for o, h in cells)
        ret, dd = med([m['cagr'] for m in b]), med([m['dd'] for m in b])
        ok = cname != ref and w >= 9 and (ret >= rb + 0.005 or dd >= rd + 0.01)
        if cname != ref:
            ok_all[cname] = ok_all[cname] and ok
        L.append(f"  {cname:26s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} {ret:+8.1%} / {med([m['sharpe'] for m in b]):4.2f} "
                 f"{dd:9.1%} {'' if cname == ref else f'{w} of 12':>13s} {'' if cname == ref else ('yes' if ok else 'no')}")
    L.append("")
L.append("verdict: " + "; ".join(f"{c}: {'PASS' if ok else 'fail'}" for c, ok in ok_all.items()))
print("\n".join(L))
