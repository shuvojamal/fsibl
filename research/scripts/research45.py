"""Research round 45: how big do single positions get, and do the big ones cause big losses?

Prompted by the VPS testnet's TRX buy on 2026-10-28: 7,475.6 TRX at 0.3319,
about 2,481 USDT, half of its 5,000 capital, because TRX's 2 x ATR stop was
only 2.1% away. Round 43 tested caps and said positions were "about 5-17% of
equity"; that was the typical case, not the range. This measures the range.

Method: round 12's simulator, growth (8 x 1%) and steady (8 x 0.5%), 6 of 8
checks, top 15, round 21's six close times x two halves. Recorded per
trade: the position's value as a share of equity at entry, and the trade's
result as a share of equity. Reported: share of trades above 25% / 40% of
equity, the largest position, which coins, and the worst single-trade losses
of big vs normal positions.

Pass bar for recommending a 25% cap, decided before running: in the growth
set-up, positions above 25% of equity make up at least 5% of trades AND at
least one of them lost more than 2% of equity (twice the planned 1%) in any
cell. Otherwise round 43's "no cap" stands.
"""
import os as _os
import pickle
from datetime import datetime, timezone
from collections import Counter

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r45'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
a = "risk=qty * (entry - plan.stop), bull=btc_bull.get(t, False))"
assert a in head
head = head.replace(a, "risk=qty * (entry - plan.stop), bull=btc_bull.get(t, False), share=qty * entry / eq_now, eq=eq_now)")
b = "trades.append(dict(t=t, pnl=p, r=p / q['risk'], sym=s, bull=q['bull']))"
assert b in head
head = head.replace(b, "trades.append(dict(t=t, pnl=p, r=p / q['risk'], sym=s, bull=q['bull'], share=q['share'], loss_eq=p / q['eq']))")


def simulate(data):
    pk = _os.path.join(ROOT, 'research', 'data', '_r45_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r45b'}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("growth 8 x 1%", 0.01), ("steady 8 x 0.5%", 0.005)]
allt = {s: [] for s, _ in SETUPS}
for o in OFFSETS:
    ns = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sname, r in SETUPS:
            _, trades = ns['run'](make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r, start=s, end=e)
            allt[sname] += [dict(x, cell=(o, half)) for x in trades]

L = ["Position size at entry (share of equity) and single-trade results; 12 cells pooled\n"]
verdict = None
for sname, r in SETUPS:
    T = allt[sname]; n = len(T)
    sh = sorted(x['share'] for x in T)
    big = [x for x in T if x['share'] > 0.25]; huge = [x for x in T if x['share'] > 0.40]
    worst_big = min((x['loss_eq'] for x in big), default=0.0)
    worst_norm = min((x['loss_eq'] for x in T if x['share'] <= 0.25), default=0.0)
    L += [sname,
          f"  trades {n}; position size median {sh[n // 2]:.0%}, 90th percentile {sh[int(.9 * n)]:.0%}, largest {sh[-1]:.0%}",
          f"  above 25% of equity: {len(big)} ({len(big) / n:.1%}); above 40%: {len(huge)} ({len(huge) / n:.1%})",
          f"  coins in the >25% trades: " + ", ".join(f"{c[:-4]} {k}" for c, k in Counter(x['sym'] for x in big).most_common(8)),
          f"  worst single-trade loss, positions >25%: {worst_big:+.2%} of equity; positions <=25%: {worst_norm:+.2%}",
          f"  trades losing more than 2x the planned risk: big {sum(x['loss_eq'] < -2 * r for x in big)}, normal {sum(x['loss_eq'] < -2 * r for x in T if x['share'] <= 0.25)}",
          f"  average result, positions >25%: {sum(x['loss_eq'] for x in big) / max(1, len(big)):+.3%} of equity; <=25%: "
          f"{sum(x['loss_eq'] for x in T if x['share'] <= 0.25) / max(1, n - len(big)):+.3%}", ""]
    if sname.startswith("growth"):
        verdict = len(big) / n >= 0.05 and worst_big < -0.02
L.append(f"verdict: {'PASS: recommend a 25% cap' if verdict else 'FAIL: no cap recommended (round 43 stands)'}")
print("\n".join(L))
