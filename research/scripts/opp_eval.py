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
cache = _os.path.join(OUT, 'candles.pkl')
if os.path.exists(cache):
    data = pickle.load(open(cache, 'rb'))
else:
    data = {s: fetch_candles(s, '1h', 5000) for s in ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']}
    pickle.dump(data, open(cache, 'wb'))
def line(tag, r, n):
    months = n / 24 / 30
    print(f"  {tag:28} trades {len(r.trades):3} ({len(r.trades)/months:4.1f}/mo) win {r.win_rate:5.1%} "
          f"PF {r.profit_factor:4.2f} ret {r.total_return:+7.2%} B&H {r.buy_hold_return:+7.2%} DD {r.max_drawdown:6.2%}")
for sym, cs in data.items():
    print(f"== {sym} ==")
    split = int(len(cs) * 0.7)
    for ms in (4, 5, 6, 7):
        p = OppParams(min_score=ms)
        line(f"min_score={ms} full", backtest.run_opportunity(cs, Opportunity(p)), len(cs))
    for ms in (5, 6):
        for rr in (1.5, 2.0, 3.0):
            p = OppParams(min_score=ms, reward_risk=rr)
            line(f"ms={ms} rr={rr} TRAIN", backtest.run_opportunity(cs[:split], Opportunity(p)), split)
            line(f"ms={ms} rr={rr} TEST ", backtest.run_opportunity(cs[split:], Opportunity(p)), len(cs)-split)
