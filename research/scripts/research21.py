"""Research round 21: is the edge a lucky choice of candle close time?

Every backtest so far used daily candles that close at 00:00 UTC, as do
the live bots. A real trend edge shouldn't care when the "day" ends. If the
results swing a lot when the close moves to 04:00, 08:00 ... 20:00 UTC,
part of the backtest is luck in the timing.

Method: hourly candles for the 30 coins that filled most of the bot's
top-15 slots in round 12 (Binance public data, 2017-08 onward), rebuilt
into daily candles closing at 00, 04, 08, 12, 16 and 20 UTC. Then the
round-12 simulator with the live rules, unchanged, on each set: the same
universe rule (top 15 by trailing-90-day volume, re-ranked quarterly),
the same costs and caveats.

The rebuilt daily candles are cached compactly (float32) in
research/data/daily_offsets.pkl.gz.
"""
import gzip
import math
import os as _os
import pickle
import statistics
import sys
import time
from array import array
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
sys.path.insert(0, ROOT)
from tradebot.data import Candle, fetch_candles

COINS = ("BTC ETH BNB XRP ADA TRX LTC DOGE LINK SOL AVAX MATIC EOS XLM SHIB PEPE SUI ETC VET NEAR "
         "BCH NEO DOT FTM ONT ZEC UNI ARB OP RUNE").split()
OFFSETS = (0, 4, 8, 12, 16, 20)
H, DAY = 3_600_000, 86_400_000
cache = _os.path.join(HERE, '..', 'data', 'daily_offsets.pkl.gz')


def build():
    def hourly(c):
        for attempt in range(3):
            try:
                return c, fetch_candles(c + 'USDT', '1h', 85000)
            except Exception as e:
                print(f"  {c}: {e}; retrying", flush=True); time.sleep(5)
        return c, []
    out = {o: {} for o in OFFSETS}
    with ThreadPoolExecutor(6) as ex:
        for c, hs in ex.map(hourly, COINS):
            print(f"  {c}: {len(hs)} hourly candles", flush=True)
            for o in OFFSETS:
                groups = {}
                for k in hs:
                    groups.setdefault((k.open_time - o * H) // DAY, []).append(k)
                days = []
                for g, ks in sorted(groups.items()):
                    if len(ks) < 20:                  # skip days with big data gaps (and the forming day)
                        continue
                    start = g * DAY + o * H
                    days.append((start, ks[0].open, max(k.high for k in ks), min(k.low for k in ks),
                                 ks[-1].close, sum(k.volume for k in ks)))
                if len(days) >= 260:
                    out[o][c + 'USDT'] = (array('q', [d[0] for d in days]),
                                          array('f', [v for d in days for v in d[1:]]))
    with gzip.open(cache, 'wb') as f:
        pickle.dump(out, f)
    return out


def unpack(packed):
    data = {}
    for s, (ts, vals) in packed.items():
        data[s] = [Candle(t, float(vals[5 * i]), float(vals[5 * i + 1]), float(vals[5 * i + 2]),
                          float(vals[5 * i + 3]), float(vals[5 * i + 4]), t + DAY - 1) for i, t in enumerate(ts)]
    return data


raw = pickle.load(gzip.open(cache)) if _os.path.exists(cache) else build()

src = open(_os.path.join(HERE, 'research12.py')).read()
head = src[:src.index('\nL = []')]


def simulate(data):
    """Round 12's simulator and universe rule on this data set."""
    pk = _os.path.join(ROOT, 'research', 'data', '_r21_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r21'}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns['run'], ns['metrics']


def yearly(curve):
    out = {}
    for t, e in curve:
        out.setdefault(datetime.fromtimestamp(t / 1000, timezone.utc).year, [e, e])[1] = e
    return {y: b / a - 1 for y, (a, b) in out.items()}


L = [f"{len(raw[0])} coins with enough history; daily candles rebuilt from hourly data\n"]
L.append(f"{'close (UTC)':12s} {'return/yr':>10s} {'max DD':>8s} {'Sharpe':>7s} {'trades':>7s} {'win':>5s} {'avg R':>6s}")
res = {}
START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)   # after every offset's warm-up
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    curve, trades = run(start=START + o * H)
    m = metrics(curve, trades)
    res[o] = (m, yearly(curve))
    L.append(f"{o:02d}:00        {m['cagr']:+9.1%} {m['dd']:8.1%} {m['sharpe']:7.2f} {m['n']:7d} {m['win']:5.0%} {m['exp_r']:+6.2f}")
cagrs = [res[o][0]['cagr'] for o in OFFSETS]; shs = [res[o][0]['sharpe'] for o in OFFSETS]
L.append(f"\nacross close times: return/yr {min(cagrs):+.1%} to {max(cagrs):+.1%} (median {statistics.median(cagrs):+.1%}), "
         f"Sharpe {min(shs):.2f} to {max(shs):.2f}")
L.append(f"live close (00:00) ranks {sorted(cagrs, reverse=True).index(cagrs[0]) + 1} of {len(OFFSETS)} by return")
years = sorted(res[0][1])
L.append("\nby year " + "".join(f"{y:>8d}" for y in years))
for o in OFFSETS:
    L.append(f"{o:02d}:00   " + "".join(f"{res[o][1].get(y, float('nan')):+8.1%}" for y in years))
print("\n".join(L))
