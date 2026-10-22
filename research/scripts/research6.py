"""Research round 6, shared-account simulation (trailing-stop scorer, daily):
  A. Pyramiding: add a second (and third) unit once the trail has moved to
     break-even, each sized by the same 1% rule against the current stop.
  B. Drawdown throttle: halve the risk per trade while equity is more than
     10% below its peak; restore when it recovers.
  C. Universe: the original 10 coins vs 10 different coins vs all 20, to see
     whether the original five/ten were a lucky pick.
"""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')      # cached candles
RES = _os.path.join(HERE, '..', 'results')   # tables written here
import os, pickle, sys, time
sys.path.insert(0, ROOT)
from tradebot.backtest import FEE, SLIPPAGE
from tradebot.data import fetch_candles
from tradebot.opportunity import Opportunity, OppParams
from datetime import datetime, timezone

d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m-%d')
orig = pickle.load(open(f'{OUT}/daily10.pkl', 'rb'))
NEW = "BNBUSDT TRXUSDT ATOMUSDT UNIUSDT NEARUSDT FILUSDT ETCUSDT XLMUSDT ALGOUSDT AAVEUSDT".split()
cache = f'{OUT}/daily_new10.pkl'
if os.path.exists(cache):
    new = pickle.load(open(cache, 'rb'))
else:
    new = {}
    for s in NEW:
        new[s] = fetch_candles(s, '1d', 1500); time.sleep(0.3)
    pickle.dump(new, open(cache, 'wb'))
both = {**orig, **new}


def portfolio(data, max_open=5, risk=0.01, capital=10000.0, start_frac=0.0,
              pyramid=0, throttle_dd=None):
    p = OppParams(risk_frac=risk)
    strats = {s: Opportunity(p).prepare(cs) for s, cs in data.items()}
    idx = {s: {c.open_time: i for i, c in enumerate(cs)} for s, cs in data.items()}
    times = sorted(set(t for s in data for t in idx[s]))
    start_t = times[int(len(times) * start_frac)]
    cash, pos, pending = capital, {}, {}
    trades, curve, peak_eq = [], [], capital

    def equity(t):
        return cash + sum(q['qty'] * data[k][idx[k][t]].close for k, q in pos.items() if t in idx[k])

    for t in times:
        if t < start_t:
            continue
        eq_now = equity(t) if curve else capital
        risk_now = risk * (0.5 if throttle_dd and eq_now < peak_eq * (1 - throttle_dd) else 1.0)
        # fills at the open
        for s, (action, plan) in list(pending.items()):
            i = idx[s].get(t)
            if i is None:
                continue
            c = data[s][i]
            if action == 'buy' and s not in pos and len(pos) < max_open:
                entry = c.open * (1 + SLIPPAGE)
                qty = min(eq_now * risk_now / (entry - plan.stop), cash * (1 - FEE) / entry)
                if qty > 0:
                    cash -= qty * entry / (1 - FEE)
                    pos[s] = dict(qty=qty, cost=qty * entry, stop=plan.stop, peak=entry, adds=0, entry=entry)
            elif action == 'add' and s in pos:
                q = pos[s]
                px = c.open * (1 + SLIPPAGE)
                qty = min(eq_now * risk_now / (px - q['stop']), cash * (1 - FEE) / px)
                if qty > 0 and px > q['stop']:
                    cash -= qty * px / (1 - FEE)
                    q['qty'] += qty; q['cost'] += qty * px; q['adds'] += 1
            elif action == 'sell' and s in pos:
                px = c.open * (1 - SLIPPAGE)
                cash += pos[s]['qty'] * px * (1 - FEE)
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
                    px = min(q['stop'], c.open) * (1 - SLIPPAGE)
                    cash += q['qty'] * px * (1 - FEE)
                    trades.append((q['cost'], q['qty'] * px)); del pos[s]
                    continue
                st.peak = max(q['peak'], c.close); q['peak'] = st.peak
                q['stop'] = st.update_stop(i, q['stop'])
                if pyramid and q['adds'] < pyramid and q['stop'] >= q['entry'] * (1 + 0.002 * (q['adds'] + 1)):
                    # trail has locked in break-even (or more): add a unit
                    pending[s] = ('add', None)
                if st.should_exit(i):
                    pending[s] = ('sell', None)
            else:
                plan = st.signal(i)
                if plan:
                    pending[s] = ('buy', plan)
        eq = equity(t)
        peak_eq = max(peak_eq, eq)
        curve.append(eq)
    for s, q in pos.items():
        trades.append((q['cost'], q['qty'] * data[s][-1].close * (1 - SLIPPAGE)))
    final = curve[-1]
    pk, dd = 0, 0
    for e in curve:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    wins = [(a, b) for a, b in trades if b * (1 - FEE) > a]
    gains = sum(b * (1 - FEE) - a for a, b in wins)
    losses = -sum(b * (1 - FEE) - a for a, b in trades if (a, b) not in wins)
    years = len(curve) / 365
    return dict(ret=final / capital - 1, cagr=(final / capital) ** (1 / years) - 1, dd=dd,
                n=len(trades), win=len(wins) / len(trades) if trades else 0, pf=gains / losses if losses else 99)


def row(label, r):
    return f"{label:44} | {r['ret']:+8.1%} | {r['cagr']:+8.1%} | {r['dd']:7.1%} | {r['n']:6} | {r['win']:5.0%} | {min(r['pf'], 99):5.2f}"


hdr = f"{'variant':44} | {'return':>8} | {'per year':>8} | {'max DD':>7} | {'trades':>6} | {'win':>5} | {'PF':>5}"
lines = ["Shared account, 10,000 USDT, max 5 open, 1% risk, trailing-stop scorer, daily.\n"]
for start, label in ((0.0, 'FULL 4 YEARS'), (0.5, 'from 2024-10'), (0.7, 'from 2025-07'), (0.8, 'from 2025-12')):
    lines.append(f"\n### {label}\n"); lines.append(hdr)
    lines.append(row('A0 baseline (round 4)', portfolio(orig, start_frac=start)))
    lines.append(row('A1 pyramid: +1 unit at break-even', portfolio(orig, start_frac=start, pyramid=1)))
    lines.append(row('A2 pyramid: up to +2 units', portfolio(orig, start_frac=start, pyramid=2)))
    lines.append(row('B1 drawdown throttle 10% (half risk)', portfolio(orig, start_frac=start, throttle_dd=0.10)))
    lines.append(row('B2 throttle 10% + pyramid 1', portfolio(orig, start_frac=start, throttle_dd=0.10, pyramid=1)))
    lines.append(row('C1 universe: other 10 coins', portfolio(new, start_frac=start)))
    lines.append(row('C2 universe: all 20 coins, max 5 open', portfolio(both, start_frac=start)))
    lines.append(row('C3 universe: all 20 coins, max 8 open', portfolio(both, max_open=8, start_frac=start)))
    bh_o = sum(cs[-1].close / cs[int(len(cs) * start)].open - 1 for cs in orig.values()) / 10
    bh_n = sum(cs[-1].close / cs[int(len(cs) * start)].open - 1 for cs in new.values()) / 10
    lines.append(f"buy & hold basket: original 10 {bh_o:+.1%}, other 10 {bh_n:+.1%}")
cs = new['BNBUSDT']
lines.append(f"\n(other-10 data {d(cs[0].open_time)} -> {d(cs[-1].close_time)}; {', '.join(NEW)})")
open(f'{RES}/research6.md', 'w').write("\n".join(lines) + "\n")
print("\n".join(lines))
