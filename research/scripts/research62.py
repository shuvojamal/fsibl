"""Research round 62: do meme coins (DOGE, SHIB, PEPE) help or hurt?

Meme coins often reach the top 15 by traded volume and so enter the bot's
list (the OKX demo holds PEPE now). They make huge, short trends and huge
reversals. Do they add winners the strategy needs, or mostly noise?

Cases: live universe vs the same with DOGE, SHIB and PEPE removed from the
data (the top 15 is then filled by the next coins). Steady and growth,
6 of 8 checks, round 12's simulator and costs, round 21's six close times x
two halves (30 coins, of which these three are meme coins).

Pass bar, decided before running (with round 53's effect-size floor):
excluding meme coins is recommended only if it has a higher Sharpe in at
least 9 of 12 cells AND adds at least 0.5 points of 2022-26 median return or
makes the median worst drop at least 1 point shallower, on both set-ups.
Also reported: the meme coins' share of trades and of profit in the live run.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r62'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

MEME = {"DOGEUSDT", "SHIBUSDT", "PEPEUSDT"}
START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
res, share = {}, {}
for o in OFFSETS:
    full = unpack(raw[o])
    for uname, data in (("live (with meme coins)", full), ("without DOGE/SHIB/PEPE", {s: c for s, c in full.items() if s not in MEME})):
        run, metrics = simulate(data)
        for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
            for sname, r in SETUPS:
                curve, trades = run(make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r, start=s, end=e)
                res[(o, half, sname, uname)] = metrics(curve, trades)
                if uname.startswith("live"):
                    k = (sname, half)
                    n, nm, pnl, pm = share.get(k, (0, 0, 0.0, 0.0))
                    share[k] = (n + len(trades), nm + sum(x['sym'] in MEME for x in trades),
                                pnl + sum(x['pnl'] for x in trades), pm + sum(x['pnl'] for x in trades if x['sym'] in MEME))

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
NAMES = ["live (with meme coins)", "without DOGE/SHIB/PEPE"]
L = ["Meme coins in or out; 8 slots, 6 checks, top 15; medians over six close times\n"]
ok_all = True
for sname, _ in SETUPS:
    ref = NAMES[0]
    rb = med([res[(o, "2022-26", sname, ref)]['cagr'] for o in OFFSETS]); rd = med([res[(o, "2022-26", sname, ref)]['dd'] for o in OFFSETS])
    L += [sname, f"  {'universe':24s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s} {'wins vs live':>13s} pass?"]
    for u in NAMES:
        a = [res[(o, "2018-21", sname, u)] for o in OFFSETS]; b = [res[(o, "2022-26", sname, u)] for o in OFFSETS]
        w = sum(res[(o, h, sname, u)]['sharpe'] > res[(o, h, sname, ref)]['sharpe'] for o, h in cells)
        ret, dd = med([m['cagr'] for m in b]), med([m['dd'] for m in b])
        ok = u != ref and w >= 9 and (ret >= rb + 0.005 or dd >= rd + 0.01)
        if u != ref:
            ok_all = ok_all and ok
        L.append(f"  {u:24s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} {ret:+8.1%} / {med([m['sharpe'] for m in b]):4.2f} "
                 f"{dd:9.1%} {'' if u == ref else f'{w} of 12':>13s} {'' if u == ref else ('yes' if ok else 'no')}")
    for h in ("2018-21", "2022-26"):
        n, nm, pnl, pm = share[(sname, h)]
        L.append(f"  live run {h}: meme coins were {nm / n:.0%} of trades and {pm / pnl:+.0%} of total profit")
    L.append("")
L.append(f"verdict: {'PASS: exclude meme coins' if ok_all else 'FAIL: keep meme coins in the list'}")
print("\n".join(L))

# Part B, added after the pass above (bar set before running it): confirm on
# round 12's 55-coin pool, both halves; Sharpe must be higher in both.
src12 = open(_os.path.join(HERE, 'research12.py')).read()
ns12 = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r62d'}
exec(src12[:src12.index('\nL = []')], ns12)
full55 = dict(ns12['data'])
L2 = ["", "Part B - round 12's 55-coin pool (00:00 closes, 2018-03 .. 2026-10):"]
confirmed = True
for sname, r in SETUPS:
    sh = {}
    for u, keep in (("live", lambda s: True), ("no meme", lambda s: s not in MEME)):
        ns12['data'].clear(); ns12['data'].update({s: c for s, c in full55.items() if keep(s)})
        row = f"  {sname:16s} {u:8s}"
        for half, (s, e) in (("2018-21", (START, SPLIT)), ("2022-26", (SPLIT, None))):
            m = ns12['metrics'](*ns12['run'](make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r, start=s, end=e))
            sh[(u, half)] = m['sharpe']
            row += f"   {half} {m['cagr']:+7.1%} / {m['sharpe']:4.2f} / {m['dd']:6.1%}"
        L2.append(row)
    confirmed = confirmed and all(sh[("no meme", h)] > sh[("live", h)] for h in ("2018-21", "2022-26"))
ns12['data'].clear(); ns12['data'].update(full55)
L2.append(f"Part B verdict: {'CONFIRMED on the 55-coin pool' if confirmed else 'NOT confirmed on the 55-coin pool'}")
print("\n".join(L2))
