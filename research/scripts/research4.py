"""Research round 4: portfolio simulation.
The earlier backtests gave each coin its own capital. A real account is one
pot shared by all coins. Here 10 coins trade from one equity, each trade
risks 1% of TOTAL equity, and a cap limits how many positions are open at
once. Trailing-stop scorer (round 3 default). Daily candles, full history
and the four test windows."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')      # cached candles
RES = _os.path.join(HERE, '..', 'results')   # tables written here
import pickle, sys
sys.path.insert(0, ROOT)
from tradebot.backtest import FEE, SLIPPAGE
from tradebot.opportunity import Opportunity, OppParams
from datetime import datetime, timezone

daily = pickle.load(open(f'{OUT}/daily10.pkl', 'rb'))
d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m-%d')


def portfolio(data, max_open, risk, capital=10000.0, start_frac=0.0, p=None):
    p = p or OppParams(risk_frac=risk)
    strats, idx = {}, {}
    for s, cs in data.items():
        strats[s] = Opportunity(p).prepare(cs)
        idx[s] = {c.open_time: i for i, c in enumerate(cs)}
    times = sorted(set(t for s in data for t in idx[s]))
    start_t = times[int(len(times) * start_frac)]
    cash, pos, pending = capital, {}, {}  # pos: sym -> dict(qty, entry, stop, peak)
    trades, equity_curve = [], []
    for t in times:
        if t < start_t:
            continue
        # 1) fills at this candle's open, decided on the previous close
        for s, (action, plan) in list(pending.items()):
            i = idx[s].get(t)
            if i is None:
                continue
            c = data[s][i]
            if action == 'buy' and s not in pos and len(pos) < max_open:
                entry = c.open * (1 + SLIPPAGE)
                eq = cash + sum(q['qty'] * data[k][idx[k][t]].close for k, q in pos.items() if t in idx[k])
                qty = min(strats[s].size(eq, entry, plan.stop), cash * (1 - FEE) / entry)
                if qty > 0:
                    cash -= qty * entry / (1 - FEE)
                    pos[s] = dict(qty=qty, entry=entry, stop=plan.stop, peak=entry, t0=t)
            elif action == 'sell' and s in pos:
                px = c.open * (1 - SLIPPAGE)
                cash += pos[s]['qty'] * px * (1 - FEE)
                trades.append((s, pos[s]['entry'], px, 'signal')); del pos[s]
        pending = {}
        # 2) stops against this candle's range, then trail update on close, then new signals
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
                    trades.append((s, q['entry'], px, 'stop')); del pos[s]
                    continue
                st.peak = max(q['peak'], c.close); q['peak'] = st.peak
                q['stop'] = st.update_stop(i, q['stop'])
                if st.should_exit(i):
                    pending[s] = ('sell', None)
            else:
                plan = st.signal(i)
                if plan:
                    pending[s] = ('buy', plan)
        eq = cash + sum(q['qty'] * data[k][idx[k][t]].close for k, q in pos.items() if t in idx[k])
        equity_curve.append(eq)
    # mark open positions to market
    for s, q in pos.items():
        px = data[s][-1].close * (1 - SLIPPAGE)
        trades.append((s, q['entry'], px, 'end'))
    final = equity_curve[-1]
    peak, dd = 0, 0
    for e in equity_curve:
        peak = max(peak, e); dd = min(dd, e / peak - 1)
    wins = [t for t in trades if t[2] / t[1] * (1 - FEE) ** 2 > 1]
    gains = sum(t[2] / t[1] * (1 - FEE) ** 2 - 1 for t in wins)
    losses = -sum(t[2] / t[1] * (1 - FEE) ** 2 - 1 for t in trades if t not in wins)
    years = len(equity_curve) / 365
    return dict(ret=final / capital - 1, cagr=(final / capital) ** (1 / years) - 1 if years > 0 else 0,
                dd=dd, n=len(trades), win=len(wins) / len(trades) if trades else 0,
                pf=gains / losses if losses else 99, years=years)


lines = ["Portfolio simulation: 10 coins from ONE account, trailing-stop scorer, 1% of total equity risked per trade.\n"]
lines.append(f"{'window':>12} | {'max open':>8} | {'risk':>5} | {'return':>8} | {'per year':>8} | {'max DD':>7} | {'trades':>6} | {'win':>5} | {'PF':>5}")
for start in (0.0, 0.5, 0.7, 0.8):
    label = 'full 4y' if start == 0 else 'from ' + d(daily['BTCUSDT'][int(len(daily['BTCUSDT']) * start)].open_time)[:7]
    for cap in (2, 3, 5, 10):
        for risk in (0.01, 0.02):
            r = portfolio(daily, cap, risk, start_frac=start)
            lines.append(f"{label:>12} | {cap:>8} | {risk:>5.0%} | {r['ret']:+8.1%} | {r['cagr']:+8.1%} | {r['dd']:7.1%} | {r['n']:6} | {r['win']:5.0%} | {min(r['pf'], 99):5.2f}")
    lines.append("")
# buy & hold of an equal-weight basket for comparison
for start in (0.0, 0.5, 0.7, 0.8):
    rets = []
    for s, cs in daily.items():
        i = int(len(cs) * start)
        rets.append(cs[-1].close / cs[i].open - 1)
    label = 'full 4y' if start == 0 else 'from ' + d(daily['BTCUSDT'][int(len(daily['BTCUSDT']) * start)].open_time)[:7]
    lines.append(f"equal-weight buy & hold basket, {label}: {sum(rets)/10:+.1%}")
open(f'{RES}/research4.md', 'w').write("\n".join(lines) + "\n")
print("\n".join(lines))
