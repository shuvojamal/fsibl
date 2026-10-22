"""Research round 8, 20-coin shared account (max 5 open, 1% risk, trailing scorer,
RSI 40-80 default now):
  A. Time exit: close a trade that has not reached +1 ATR after N days.
  B. Re-entry cooldown: after a stop-out, wait N days before re-entering that coin.
  C. Third universe: 10 more coins never used before.
"""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')      # cached candles
RES = _os.path.join(HERE, '..', 'results')   # tables written here
import os, pickle, sys, time
sys.path.insert(0, ROOT)
from tradebot.data import fetch_candles
from tradebot.opportunity import Opportunity, OppParams
src = open(f'{HERE}/research7.py').read().split("WINDOWS = ")[0]
ns = {}; exec(src, ns)
orig = pickle.load(open(f'{OUT}/daily10.pkl', 'rb')); new = pickle.load(open(f'{OUT}/daily_new10.pkl', 'rb'))
THIRD = "SHIBUSDT SANDUSDT MANAUSDT AXSUSDT EOSUSDT VETUSDT HBARUSDT ICPUSDT GRTUSDT THETAUSDT".split()
cache = f'{OUT}/daily_third10.pkl'
if os.path.exists(cache):
    third = pickle.load(open(cache, 'rb'))
else:
    third = {}
    for s in THIRD:
        try:
            third[s] = fetch_candles(s, '1d', 1500); time.sleep(0.3)
        except Exception as e:
            print("skip", s, e)
    pickle.dump(third, open(cache, 'wb'))
from tradebot.backtest import FEE, SLIPPAGE


def portfolio2(data, make, max_open=5, risk=0.01, capital=10000.0, start_frac=0.0,
               time_exit_days=0, cooldown_days=0):
    strats = {s: make().prepare(cs) for s, cs in data.items()}
    idx = {s: {c.open_time: i for i, c in enumerate(cs)} for s, cs in data.items()}
    times = sorted(set(t for s in data for t in idx[s]))
    start_t = times[int(len(times) * start_frac)]
    cash, pos, pending, trades, curve = capital, {}, {}, [], []
    last_stop = {}  # sym -> index of the candle it was stopped out on
    eq_of = lambda t: cash + sum(q['qty'] * data[k][idx[k][t]].close for k, q in pos.items() if t in idx[k])
    for t in times:
        if t < start_t:
            continue
        eq_now = curve[-1] if curve else capital
        for s, (action, plan) in list(pending.items()):
            i = idx[s].get(t)
            if i is None:
                continue
            c = data[s][i]
            if action == 'buy' and s not in pos and len(pos) < max_open:
                entry = c.open * (1 + SLIPPAGE)
                qty = min(eq_now * risk / (entry - plan.stop), cash * (1 - FEE) / entry)
                if qty > 0:
                    cash -= qty * entry / (1 - FEE)
                    pos[s] = dict(qty=qty, cost=qty * entry, stop=plan.stop, peak=entry, entry=entry, i0=i, atr0=entry - plan.stop)
            elif action == 'sell' and s in pos:
                px = c.open * (1 - SLIPPAGE); cash += pos[s]['qty'] * px * (1 - FEE)
                trades.append((pos[s]['cost'], pos[s]['qty'] * px)); del pos[s]
        pending = {}
        for s, cs in data.items():
            i = idx[s].get(t)
            if i is None:
                continue
            c, st = cs[i], strats[s]
            if s in pos:
                q = pos[s]
                if c.low <= q['stop']:
                    px = min(q['stop'], c.open) * (1 - SLIPPAGE); cash += q['qty'] * px * (1 - FEE)
                    trades.append((q['cost'], q['qty'] * px)); del pos[s]; last_stop[s] = i; continue
                st.peak = max(q['peak'], c.close); q['peak'] = st.peak
                q['stop'] = st.update_stop(i, q['stop'])
                stale = time_exit_days and (i - q['i0'] >= time_exit_days) and (q['peak'] < q['entry'] + 0.5 * q['atr0'])
                if st.should_exit(i) or stale:
                    pending[s] = ('sell', None)
            else:
                if cooldown_days and s in last_stop and i - last_stop[s] < cooldown_days:
                    continue
                plan = st.signal(i)
                if plan:
                    pending[s] = ('buy', plan)
        curve.append(eq_of(t))
    for s, q in pos.items():
        trades.append((q['cost'], q['qty'] * data[s][-1].close * (1 - SLIPPAGE)))
    final = curve[-1]; pk = dd = 0
    for e in curve:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    wins = [(a, b) for a, b in trades if b * (1 - FEE) > a]
    g = sum(b * (1 - FEE) - a for a, b in wins); l = -sum(b * (1 - FEE) - a for a, b in trades if (a, b) not in wins)
    return dict(ret=final / capital - 1, dd=dd, n=len(trades), win=len(wins) / max(1, len(trades)), pf=g / l if l else 99)


WINDOWS = [(0.0, 'full 4y'), (0.5, 'from 2024-10'), (0.7, 'from 2025-07'), (0.8, 'from 2025-12')]
def line(label, data, **kw):
    cells = []
    for w, _ in WINDOWS:
        r = portfolio2(data, lambda: Opportunity(OppParams()), start_frac=w, **kw)
        cells.append(f"{r['ret']:+7.1%} {r['dd']:6.1%} {r['n']:4}t {r['pf']:4.2f}")
    return f"{label:36} | " + " | ".join(cells)

both = {**orig, **new}
hdr = f"{'variant':36} | " + " | ".join(f"{l:>25}" for _, l in WINDOWS)
lines = ["20 coins, max 5 open, 1% risk, RSI 40-80. Cells: return, max DD, trades, PF.\n", hdr]
lines.append(line('baseline (round 7 default)', both))
lines.append("\n# A. time exit: sell if no +0.5 ATR progress after N days")
for n in (10, 20, 40):
    lines.append(line(f"time exit {n} days", both, time_exit_days=n))
lines.append("\n# B. cooldown after a stop-out")
for n in (3, 7, 14):
    lines.append(line(f"cooldown {n} days", both, cooldown_days=n))
lines.append("\n# C. third universe (never used before)")
lines.append(line(f"third 10: {', '.join(k[:-4] for k in third)}", third))
bh = [sum(cs[-1].close / cs[int(len(cs) * w)].open - 1 for cs in third.values()) / len(third) for w, _ in WINDOWS]
lines.append(f"{'buy & hold third 10':36} | " + " | ".join(f"{b:>+25.1%}" for b in bh))
lines.append(line('all 30 coins, max 5 open', {**both, **third}))
lines.append(line('all 30 coins, max 8 open', {**both, **third}, max_open=8))
open(f'{RES}/research8.md', 'w').write("\n".join(lines) + "\n")
print("\n".join(lines))
