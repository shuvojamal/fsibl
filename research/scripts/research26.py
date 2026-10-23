"""Research round 26: hold or trade? Buy-and-hold vs the live rules, coin by coin.

The owner asked whether crypto is good to simply hold for the long term.
For every coin in round 12's 55-coin pool, compare:
  - buy and hold from its first full year of data (or 2018-03 if older)
    to today: total return, the deepest drop from a peak, and how far below
    its all-time high it is now;
  - the live rules traded on that one coin alone (1% risk per trade, all
    capital available to that coin, same costs as round 12).
Questions: how many coins beat holding cash over the period, how many are
still far below their old highs, and on how many does the trend rule end
ahead of holding, or lose less in the worst drop?

Big caveat, in holding's favour: the pool is today's list. Coins that died
and were delisted (LUNA, FTT and many others) are missing, so the real
picture for holders of a random 2018 basket was worse than shown.
"""
import os as _os
import pickle
import statistics
import sys
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
sys.path.insert(0, ROOT)
from tradebot.backtest import run_opportunity
from tradebot.opportunity import Opportunity, OppParams

data = pickle.load(open(_os.path.join(HERE, '..', 'data', 'daily_long.pkl'), 'rb'))
START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m')

rows = []
for s, cs in data.items():
    i0 = next((i for i, c in enumerate(cs) if c.open_time >= START and i >= 365), None)
    if i0 is None or len(cs) - i0 < 365:
        continue
    closes = [c.close for c in cs[i0:]]
    hold = closes[-1] / cs[i0].open - 1
    peak, dd = closes[0], 0.0
    for c in closes:
        peak = max(peak, c); dd = min(dd, c / peak - 1)
    ath = max(c.high for c in cs)
    from_ath = closes[-1] / ath - 1
    res = run_opportunity(cs, Opportunity(OppParams()), capital=10000.0, start=i0)
    rows.append(dict(sym=s[:-4], since=d(cs[i0].open_time), hold=hold, hold_dd=dd, from_ath=from_ath,
                     bot=res.total_return, bot_dd=res.max_drawdown, trades=len(res.trades)))

rows.sort(key=lambda r: -r['hold'])
L = [f"{len(rows)} coins with at least two years of data; buy & hold from 2018-03 or the coin's second year, to 2026-10\n",
     f"{'coin':7s} {'since':8s} {'hold':>9s} {'hold worst drop':>16s} {'now vs all-time high':>21s} {'bot (1 coin)':>13s} {'bot worst drop':>15s} {'trades':>7s}"]
for r in rows:
    L.append(f"{r['sym']:7s} {r['since']:8s} {r['hold']:+9.0%} {r['hold_dd']:16.0%} {r['from_ath']:21.0%} {r['bot']:+13.0%} {r['bot_dd']:15.0%} {r['trades']:7d}")
n = len(rows)
L.append("")
L.append(f"holding made money on {sum(r['hold'] > 0 for r in rows)} of {n} coins; lost more than half on {sum(r['hold'] < -0.5 for r in rows)}; "
         f"median hold return {statistics.median(r['hold'] for r in rows):+.0%}")
L.append(f"every coin fell at least {max(r['hold_dd'] for r in rows):.0%} from a peak while held; median worst drop {statistics.median(r['hold_dd'] for r in rows):.0%}")
L.append(f"{sum(r['from_ath'] < -0.5 for r in rows)} of {n} coins are now more than 50% below their all-time high; "
         f"{sum(r['from_ath'] < -0.8 for r in rows)} are more than 80% below")
L.append(f"trend rule on one coin made money on {sum(r['bot'] > 0 for r in rows)} of {n}; median {statistics.median(r['bot'] for r in rows):+.0%}; "
         f"median worst drop {statistics.median(r['bot_dd'] for r in rows):.0%}")
L.append(f"trend rule ended ahead of holding on {sum(r['bot'] > r['hold'] for r in rows)} of {n} coins; "
         f"had the smaller worst drop on {sum(r['bot_dd'] > r['hold_dd'] for r in rows)} of {n}")
print("\n".join(L))
