"""Research round 9: a hindsight-free universe rule.
Pool of ~45 Binance USDT pairs. Each quarter, rank the pool by trailing
90-day dollar volume (from the candles themselves, so no external data and
no look-ahead) and allow NEW entries only in the top N for the next quarter.
Open positions keep running. Compare with the hand-picked 20."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')      # cached candles
RES = _os.path.join(HERE, '..', 'results')   # tables written here
import os, pickle, sys, time
sys.path.insert(0, ROOT)
from tradebot.data import fetch_candles
from tradebot.opportunity import Opportunity, OppParams
from tradebot.backtest import FEE, SLIPPAGE
from datetime import datetime, timezone
d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m-%d')

pool = {}
for f in ('daily10.pkl', 'daily_new10.pkl', 'daily_third10.pkl'):
    pool.update(pickle.load(open(f'{OUT}/{f}', 'rb')))
EXTRA = "BCHUSDT SUIUSDT PEPEUSDT ARBUSDT OPUSDT APTUSDT INJUSDT FETUSDT TIAUSDT SEIUSDT ZECUSDT CRVUSDT RUNEUSDT IMXUSDT STXUSDT".split()
cache = f'{OUT}/daily_extra15.pkl'
if os.path.exists(cache):
    extra = pickle.load(open(cache, 'rb'))
else:
    extra = {}
    for s in EXTRA:
        try:
            cs = fetch_candles(s, '1d', 1500); time.sleep(0.3)
            if len(cs) >= 300:
                extra[s] = cs
        except Exception as e:
            print('skip', s, e)
    pickle.dump(extra, open(cache, 'wb'))
pool.update(extra)
HAND20 = "BTCUSDT ETHUSDT SOLUSDT XRPUSDT DOGEUSDT ADAUSDT LINKUSDT AVAXUSDT DOTUSDT LTCUSDT BNBUSDT TRXUSDT ATOMUSDT UNIUSDT NEARUSDT FILUSDT ETCUSDT XLMUSDT ALGOUSDT AAVEUSDT".split()


def portfolio(data, allowed_fn, max_open=5, risk=0.01, capital=10000.0, start_frac=0.0):
    """allowed_fn(sym, t) -> may this symbol open a NEW position at time t?"""
    strats = {s: Opportunity(OppParams()).prepare(cs) for s, cs in data.items()}
    idx = {s: {c.open_time: i for i, c in enumerate(cs)} for s, cs in data.items()}
    times = sorted(set(t for s in data for t in idx[s]))
    start_t = times[int(len(times) * start_frac)]
    cash, pos, pending, trades, curve = capital, {}, {}, [], []
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
                    pos[s] = dict(qty=qty, cost=qty * entry, stop=plan.stop, peak=entry)
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
                    trades.append((q['cost'], q['qty'] * px)); del pos[s]; continue
                st.peak = max(q['peak'], c.close); q['peak'] = st.peak
                q['stop'] = st.update_stop(i, q['stop'])
                if st.should_exit(i):
                    pending[s] = ('sell', None)
            elif allowed_fn(s, t):
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
    return dict(ret=final / capital - 1, dd=dd, n=len(trades), pf=g / l if l else 99)


# quarterly volume ranking, computed once
QUARTER = 90 * 86_400_000
t0 = min(cs[0].open_time for cs in pool.values())
tN = max(cs[-1].open_time for cs in pool.values())
quarters = list(range(t0, tN + QUARTER, QUARTER))
rank_at = {}  # quarter start -> list of symbols ranked by trailing-90d dollar volume
for qs in quarters:
    vols = {}
    for s, cs in pool.items():
        dv = sum(c.volume * c.close for c in cs if qs - QUARTER <= c.open_time < qs)
        if dv > 0:
            vols[s] = dv
    rank_at[qs] = sorted(vols, key=vols.get, reverse=True)


def top_n(n):
    def allowed(s, t):
        qs = quarters[max(0, min(len(quarters) - 1, (t - t0) // QUARTER))]
        return s in rank_at[qs][:n]
    return allowed


WINDOWS = [(0.0, 'full 4y'), (0.5, 'from 2024-10'), (0.7, 'from 2025-07'), (0.8, 'from 2025-12')]
def line(label, data, allowed, **kw):
    cells = []
    for w, _ in WINDOWS:
        r = portfolio(data, allowed, start_frac=w, **kw)
        cells.append(f"{r['ret']:+7.1%} {r['dd']:6.1%} {r['n']:4}t {r['pf']:4.2f}")
    return f"{label:40} | " + " | ".join(cells)

hdr = f"{'universe rule':40} | " + " | ".join(f"{l:>25}" for _, l in WINDOWS)
lines = [f"Pool of {len(pool)} coins. Max 5 open, 1% risk, RSI 40-80. Cells: return, max DD, trades, PF.\n", hdr]
hand = {s: pool[s] for s in HAND20}
lines.append(line('hand-picked 20 (current demo list)', hand, lambda s, t: True))
lines.append(line(f'whole pool ({len(pool)}), no rule', pool, lambda s, t: True))
for n in (10, 15, 20, 30):
    lines.append(line(f'top {n} by trailing-90d volume, quarterly', pool, top_n(n)))
lines.append(line('top 20 by volume, max 8 open', pool, top_n(20), max_open=8))
lines.append("\nWho is in the top 15 by volume right now: " + ", ".join(s[:-4] for s in rank_at[quarters[-1]][:15]))
lines.append("Top 15 two years ago:                    " + ", ".join(s[:-4] for s in rank_at[quarters[-9]][:15]))
open(f'{RES}/research9.md', 'w').write("\n".join(lines) + "\n")
print("\n".join(lines))
