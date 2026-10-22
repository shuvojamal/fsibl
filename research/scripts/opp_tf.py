import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')      # cached candles
RES = _os.path.join(HERE, '..', 'results')   # tables written here
import sys, pickle, os
sys.path.insert(0, ROOT)
from tradebot import backtest
from tradebot.data import fetch_candles
from tradebot.opportunity import Opportunity, OppParams
cache = _os.path.join(OUT, 'candles_tf.pkl')
if os.path.exists(cache):
    data = pickle.load(open(cache, 'rb'))
else:
    data = {(s, tf): fetch_candles(s, tf, n) for s in ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'] for tf, n in [('4h', 5000), ('1d', 1500)]}
    pickle.dump(data, open(cache, 'wb'))
hours = {'4h': 4, '1d': 24}
def line(tag, r, n, tf):
    months = n * hours[tf] / 24 / 30
    print(f"  {tag:22} trades {len(r.trades):3} ({len(r.trades)/months:4.1f}/mo) win {r.win_rate:5.1%} "
          f"PF {r.profit_factor:4.2f} ret {r.total_return:+8.2%} B&H {r.buy_hold_return:+8.2%} DD {r.max_drawdown:6.2%}")
for (sym, tf), cs in data.items():
    from datetime import datetime, timezone
    d = lambda ms: datetime.fromtimestamp(ms/1000, timezone.utc).strftime('%Y-%m-%d')
    print(f"== {sym} {tf}: {d(cs[0].open_time)} -> {d(cs[-1].close_time)} ({len(cs)} candles) ==")
    split = int(len(cs) * 0.7)
    for ms in (5, 6, 7):
        p = OppParams(min_score=ms)
        line(f"ms={ms} FULL", backtest.run_opportunity(cs, Opportunity(p)), len(cs), tf)
        line(f"ms={ms}   train", backtest.run_opportunity(cs[:split], Opportunity(p)), split, tf)
        line(f"ms={ms}   test", backtest.run_opportunity(cs[split:], Opportunity(p)), len(cs)-split, tf)
