"""Research round 65: what does the backtest say about the live period itself?

The VPS testnet (growth, 8 x 1%) lost 6.1% from 2026-10-23 to now (six
trades, five losers). Round 63's data stopped on 2026-10-21. This downloads
fresh daily candles (Binance public data, 00:00 UTC closes, the live bot's
schedule) for round 21's 30 coins and runs round 12's simulator over
exactly the live period, from a flat start on 2026-10-23, so the live
result can be compared with what the rules "should" have done.

Pass bar (a consistency test, decided before running): the live testnet is
"consistent with the rules" if its result is within 3 points of the
backtest's over the same days. A larger gap would point to execution
(testnet prices, skipped buys) rather than the market.
Data saved to research/data/daily_live_period.pkl (30 coins, ~420 days).
"""
import csv
import os as _os
import pickle
import time
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
import sys
sys.path.insert(0, ROOT)
from tradebot.data import fetch_candles
from tradebot.opportunity import Opportunity, OppParams

COINS = ("BTC ETH BNB XRP ADA TRX LTC DOGE LINK SOL AVAX MATIC EOS XLM SHIB PEPE SUI ETC VET NEAR "
         "BCH NEO DOT FTM ONT ZEC UNI ARB OP RUNE").split()
CACHE = _os.path.join(ROOT, 'research', 'data', 'daily_live_period.pkl')
if _os.path.exists(CACHE):
    data = pickle.load(open(CACHE, 'rb'))
else:
    data = {}
    for c in COINS:
        try:
            cs = fetch_candles(c + 'USDT', '1d', 420)
            if len(cs) >= 260:
                data[c + 'USDT'] = cs
        except Exception as e:
            print(f"  {c}: skipped ({e})")
        time.sleep(0.2)
    pickle.dump(data, open(CACHE, 'wb'))

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r65b'}
exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {CACHE!r}"), ns)

START = int(datetime(2026, 10, 23, tzinfo=timezone.utc).timestamp() * 1000)
end = max(cs[-1].open_time for cs in data.values())
rows = list(csv.DictReader(open(_os.path.join(ROOT, 'binance_state', 'equity.csv'))))
live = float(rows[-1]['equity']) / 5000.0 - 1
L = [f"{len(data)} coins; live period 2026-10-23 .. {datetime.fromtimestamp(end / 1000, timezone.utc):%Y-%m-%d} (last closed daily candle)\n"]
res = {}
for sname, r in (("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)):
    curve, trades = ns['run'](make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r, capital=5000.0, start=START)
    ret = curve[-1][1] / 5000.0 - 1
    res[sname] = ret
    wins = sum(x['pnl'] > 0 for x in trades)
    L.append(f"{sname:16s} backtest over the live period: {ret:+.1%}  ({len(trades)} closed trades, {wins} winners)"
             + "".join(f"\n    {datetime.fromtimestamp(x['t'] / 1000, timezone.utc):%m-%d} {x['sym'][:-4]:5s} {x['r']:+.2f}R" for x in trades))
L.append(f"\nlive testnet (growth) over the same period: {live:+.1%} (equity.csv, last row {rows[-1]['time'][:10]})")
gap = live - res["growth 8 x 1%"]
L.append(f"gap live - backtest: {gap:+.1%} -> {'CONSISTENT with the rules' if abs(gap) <= 0.03 else 'NOT consistent: check execution'}")
print("\n".join(L))
