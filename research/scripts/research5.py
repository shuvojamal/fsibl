"""Research round 5: redo the per-coin window tests of rounds 2B and 3 with the
indicators warmed up on the full series, so each test window can trade from
its first day instead of being blind for its first 200 days."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')      # cached candles
RES = _os.path.join(HERE, '..', 'results')   # tables written here
import pickle, sys
sys.path.insert(0, ROOT)
from tradebot import backtest
from tradebot.opportunity import Opportunity, OppParams
from datetime import datetime, timezone

daily = pickle.load(open(f'{OUT}/daily10.pkl', 'rb'))
d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m-%d')
WINDOWS = [0.5, 0.6, 0.7, 0.8, 0.9]
VARIANTS = {
    'fixed 3:1 target + EMA exit': lambda: Opportunity(OppParams(trail_atr=0)),
    'trailing stop 2 ATR': lambda: Opportunity(OppParams(trail_atr=2.0)),
    'trailing stop 3 ATR (default)': lambda: Opportunity(OppParams(trail_atr=3.0)),
    'trailing stop 4 ATR': lambda: Opportunity(OppParams(trail_atr=4.0)),
}
lines = ["Per-coin tests, indicators warmed on the full history, trading from the window start. 10 coins, 1% risk.",
         "Cells: average return / coins profitable / total trades.\n"]
labels = ['from ' + d(daily['BTCUSDT'][int(len(daily['BTCUSDT']) * w)].open_time)[:7] for w in WINDOWS]
lines.append(f"{'variant':30} | " + " | ".join(f"{l:>18}" for l in labels))
for name, make in VARIANTS.items():
    cells = []
    for w in WINDOWS:
        rets, n = [], 0
        for s, cs in daily.items():
            r = backtest.run_opportunity(cs, make(), start=int(len(cs) * w))
            rets.append(r.total_return); n += len(r.trades)
        cells.append(f"{sum(rets)/10:+6.1%} {sum(x > 0 for x in rets):>2}/10 {n:>4}t")
    lines.append(f"{name:30} | " + " | ".join(f"{c:>18}" for c in cells))
bh = []
for w in WINDOWS:
    bh.append(sum(cs[-1].close / cs[int(len(cs) * w)].open - 1 for cs in daily.values()) / 10)
lines.append(f"{'buy & hold (avg of 10 coins)':30} | " + " | ".join(f"{b:>+18.1%}" for b in bh))

lines.append("\nTrailing 3 ATR, per coin, most recent window (" + labels[-1] + "):")
for s, cs in daily.items():
    r = backtest.run_opportunity(cs, Opportunity(OppParams()), start=int(len(cs) * 0.9))
    lines.append(f"  {s:9} {r.total_return:+7.1%}  trades {len(r.trades):2}  win {r.win_rate:4.0%}  maxDD {r.max_drawdown:6.1%}  B&H {r.buy_hold_return:+7.1%}")
lines.append("\nSignal check: which coins would the default strategy have entered in the last 30 days?")
for s, cs in daily.items():
    st = Opportunity(OppParams()).prepare(cs)
    hits = [(d(cs[i].open_time), st.signal(i).score) for i in range(len(cs) - 30, len(cs)) if st.signal(i)]
    lines.append(f"  {s:9} " + (", ".join(f"{t} (score {sc})" for t, sc in hits) if hits else "none"))
open(f'{RES}/research5.md', 'w').write("\n".join(lines) + "\n")
print("\n".join(lines))
