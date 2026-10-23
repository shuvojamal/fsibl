"""Research round 18: the live rules on XM-style CFD markets (gold, indices, oil, forex).

The owner asked about running the bot on an XM demo account (MetaTrader 5,
CFDs). Before building that, does the strategy survive those markets and
their costs? CFDs charge an overnight financing fee ("swap") for every night
a position is open, and this strategy holds trades for weeks.

Markets (Yahoo Finance daily data, cached in research/data/xm_markets.pkl):
gold, silver, crude oil, S&P 500, Nasdaq 100, DAX, Nikkei, EUR/USD, GBP/USD,
USD/JPY, AUD/USD. Futures/index levels stand in for the CFD prices.

Rules: exactly the live crypto rules, untuned (5 of 8 checks, 2xATR stop,
3xATR trailing stop, 1% risk, max 5 open). Forex has no volume data, so the
volume check can never pass there (at most 7 of 8). Costs: round 12's 0.1%
fee + 0.05% slippage per side (wider than typical CFD spreads on these
markets, so conservative), plus a swap charged on the open notional every
trading day, swept at 0%, 3% and 6% a year (long gold and index CFDs at
offshore brokers typically cost roughly 3-8% a year; forex swaps follow the
interest-rate gap and can be positive or negative).

Scored 2010-01 onward; split check 2010-2017 vs 2018-2026.
"""
import json
import math
import os as _os
import pickle
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research12.py')).read()
head = src[:src.index('\nL = []')]
# daily swap on the open notional: insert at the top of the simulator's day loop
# Markets close on different holidays, so value a position at its last known
# close on days its market is shut (round 12's crypto data never has gaps).
head = head.replace("    eq_of = lambda t: cash + sum(q['qty'] * data[k][idx[k][t]].close for k, q in pos.items() if t in idx[k])",
                    "    last_px = {}\n"
                    "    eq_of = lambda t: cash + sum(q['qty'] * last_px.get(k, q['cost'] / q['qty']) for k, q in pos.items())", 1)
head = head.replace("    for t in times:\n", "    for t in times:\n"
                    "        for k in pos:\n"
                    "            if t in idx[k]:\n"
                    "                last_px[k] = data[k][idx[k][t]].close\n"
                    "        cash -= sum(q['qty'] * last_px.get(k, q['cost'] / q['qty']) for k, q in pos.items()) * SWAP / 252\n", 1)
assert "last_px = {}" in head and "SWAP / 252" in head
ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r12', 'SWAP': 0.0}
exec(head, ns)
d = ns['d']
from tradebot.data import Candle

MARKETS = {"GOLD": "GC=F", "SILVER": "SI=F", "OIL": "CL=F", "US500": "^GSPC", "US100": "^NDX", "GER40": "^GDAXI",
           "JP225": "^N225", "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "JPY=X", "AUDUSD": "AUDUSD=X"}
cache = _os.path.join(HERE, '..', 'data', 'xm_markets.pkl')
if _os.path.exists(cache):
    mk = pickle.load(open(cache, 'rb'))
else:
    mk = {}
    for name, tick in MARKETS.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(tick)}?period1=946684800&period2=1792800000&interval=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        r = json.load(urllib.request.urlopen(req, timeout=30))["chart"]["result"][0]
        q = r["indicators"]["quote"][0]
        cs = []
        for i, ts in enumerate(r["timestamp"]):
            o, h, lo, c, v = q["open"][i], q["high"][i], q["low"][i], q["close"][i], q["volume"][i]
            if None in (o, h, lo, c) or min(o, h, lo, c) <= 0:
                continue
            day = ts // 86400 * 86_400_000
            if cs and day <= cs[-1].open_time:
                continue
            cs.append(Candle(day, o, max(h, o, c), min(lo, o, c), c, float(v or 0), day + 86_399_999))
        mk[name] = cs
    pickle.dump(mk, open(cache, 'wb'))

START = int(datetime(2010, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2018, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def use(markets):
    """Point round 12's simulator at these markets, all always eligible."""
    data = {m: mk[m] for m in markets}
    ns['data'] = data
    t0 = min(cs[0].open_time for cs in data.values())
    ns['t0'], ns['quarters'], ns['QUARTER'] = t0, [t0], 10 ** 15
    ns['rank_at'] = {t0: list(data)}


def stats(curve):
    eq = [e for _, e in curve]
    rets = [eq[i] / eq[i - 1] - 1 for i in range(1, len(eq))]
    yrs = (curve[-1][0] - curve[0][0]) / 86_400_000 / 365.25
    pk = dd = 0
    for e in eq:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    mu = sum(rets) / len(rets); sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / len(rets))
    return (eq[-1] / eq[0]) ** (1 / yrs) - 1, dd, mu / sd * math.sqrt(252) if sd else 0


def line(curve, trades):
    c, dd, sh = stats(curve)
    rs = [x['r'] for x in trades]
    pf = sum(r for r in rs if r > 0) / -sum(r for r in rs if r < 0) if any(r < 0 for r in rs) else 99
    return f"{c:+6.1%}/yr  maxDD {dd:6.1%}  Sharpe {sh:4.2f}  trades {len(rs):3d}  win {sum(r > 0 for r in rs) / max(1, len(rs)):4.0%}  PF {pf:4.2f}"


L = [f"Data: {', '.join(f'{m} {d(cs[0].open_time)[:4]}' for m, cs in mk.items())}; scored from 2010-01\n"]
L.append("## 1. Each market alone (1% risk per trade), swap 0% / 3% / 6% a year, vs buy & hold")
for m, cs in mk.items():
    use([m])
    i0 = next(i for i, c in enumerate(cs) if c.open_time >= START)
    bh = (cs[-1].close / cs[i0].open) ** (365.25 * 86_400_000 / (cs[-1].open_time - cs[i0].open_time)) - 1
    out = []
    for sw in (0.0, 0.03, 0.06):
        ns['SWAP'] = sw
        cv, tr = ns['run'](top=1, start=START, max_open=1)
        out.append(stats(cv)[0])
    ns['SWAP'] = 0.03
    cv, tr = ns['run'](top=1, start=START, max_open=1)
    L.append(f"  {m:7s} swap0 {out[0]:+6.1%}  swap3 {out[1]:+6.1%}  swap6 {out[2]:+6.1%}/yr   (at 3%: {line(cv, tr)})   buy&hold {bh:+6.1%}/yr")

groups = {"gold+indices+oil (6)": ["GOLD", "SILVER", "OIL", "US500", "US100", "GER40"],
          "all 11": list(mk)}
L.append("\n## 2. Portfolio: all markets eligible, max 5 open, 1% risk (the live crypto settings)")
for gname, ms in groups.items():
    use(ms)
    for sw in (0.0, 0.03, 0.06):
        ns['SWAP'] = sw
        cv, tr = ns['run'](top=len(ms), start=START)
        L.append(f"  {gname:22s} swap {sw:.0%}: {line(cv, tr)}")
    ns['SWAP'] = 0.03
    for label, s, e in (("2010-2017", START, SPLIT), ("2018-2026", SPLIT, None)):
        cv, tr = ns['run'](top=len(ms), start=s, end=e)
        L.append(f"     {label} at swap 3%: {line(cv, tr)}")

L.append("\n## 3. Same portfolios at typical CFD costs (0.02% spread + 0.02% slippage per side instead of 0.15%)")
for gname, ms in groups.items():
    use(ms)
    for sw in (0.0, 0.03, 0.06):
        ns['SWAP'] = sw
        cv, tr = ns['run'](top=len(ms), start=START, fee=0.0002, slip=0.0002)
        L.append(f"  {gname:22s} swap {sw:.0%}: {line(cv, tr)}")
    ns['SWAP'] = 0.03
    for label, s, e in (("2010-2017", START, SPLIT), ("2018-2026", SPLIT, None)):
        cv, tr = ns['run'](top=len(ms), start=s, end=e, fee=0.0002, slip=0.0002)
        L.append(f"     {label} at swap 3%: {line(cv, tr)}")
L.append("  buy & hold for reference, 2010-2026: US500 +12.2%/yr, US100 +17.7%/yr, GOLD +7.9%/yr (no swaps: futures/ETF-style)")

L.append("\nFor comparison, the crypto book (round 12, 2017-2026): +22.7%/yr, maxDD -31.4%, Sharpe 0.97 (365-day basis)")
print("\n".join(L))
