"""Research round 17: gold (PAXG) with the live rules.

PAXG is a token backed by one troy ounce of gold (Paxos), traded against
USDT on Binance and OKX, so the bot could trade gold with no new broker.

Questions:
  1. Do the live rules work on PAXG alone (vs holding PAXG)?
  2. Is PAXG different enough from crypto to help: correlation with BTC and
     with the bot's own daily returns.
  3. Does adding PAXG as an always-eligible extra symbol (alongside the top
     15 by volume) improve the whole book? Same rules, same 5 slots, 1% risk.
  4. Liquidity: is there enough volume to trade it?

Same simulator, costs and caveats as round 12 (reused). PAXG daily candles
from Binance's public API, cached in research/data/paxg.pkl. Window: from
PAXG's listing (2020-09) plus the 200-day warm-up, i.e. scored from 2021-04.
"""
import math
import os as _os
import pickle
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research12.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r12'}
exec(src[:src.index('\nL = []')], ns)
data, run, rank_at, d = ns['data'], ns['run'], ns['rank_at'], ns['d']
from tradebot.backtest import run_opportunity
from tradebot.data import fetch_candles
from tradebot.opportunity import Opportunity, OppParams

cache = _os.path.join(HERE, '..', 'data', 'paxg.pkl')
if _os.path.exists(cache):
    paxg = pickle.load(open(cache, 'rb'))
else:
    paxg = fetch_candles('PAXGUSDT', '1d', 3000)
    pickle.dump(paxg, open(cache, 'wb'))
# Stop at the last day the cached crypto data has: a day present only for PAXG
# would value every open crypto position at zero in the simulator.
END = data['BTCUSDT'][-1].open_time
paxg = [c for c in paxg if c.open_time <= END]
DAY = 86_400_000
START = paxg[0].open_time + 200 * DAY


def stats(curve):
    eq = [e for _, e in curve]
    rets = [eq[i] / eq[i - 1] - 1 for i in range(1, len(eq))]
    yrs = len(eq) / 365
    pk = dd = 0
    for e in eq:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    mu = sum(rets) / len(rets); sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / len(rets))
    return dict(cagr=(eq[-1] / eq[0]) ** (1 / yrs) - 1, dd=dd, sharpe=mu / sd * math.sqrt(365) if sd else 0)


def corr(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))


def by_year(curve):
    out = {}
    for t, e in curve:
        out.setdefault(d(t)[:4], [e, e])[1] = e
    return {y: b / a - 1 for y, (a, b) in out.items()}


L = [f"PAXG daily candles {d(paxg[0].open_time)} -> {d(paxg[-1].open_time)} ({len(paxg)} days); scored from {d(START)}\n"]

# 4. liquidity
vols = [c.volume * c.close for c in paxg[-90:]]
L.append(f"Binance PAXG dollar volume, last 90 days: median {sorted(vols)[45] / 1e6:.1f}M USD/day "
         f"(the bot's orders are ~1,000 USD, so liquidity is ample)")
top15_cut = []
for qs, ranked in rank_at.items():
    if qs >= START and len(ranked) >= 15:
        sym = ranked[14]
        top15_cut.append(sum(c.volume * c.close for c in data[sym] if qs - 90 * DAY <= c.open_time < qs) / 90)
L.append(f"for comparison, the 15th coin by volume trades a median {sorted(top15_cut)[len(top15_cut) // 2] / 1e6:.0f}M USD/day: "
         f"PAXG would never make the top 15 on its own, so it must be added as a fixed extra symbol\n")

# 1. PAXG alone
i0 = next(i for i, c in enumerate(paxg) if c.open_time >= START)
res = run_opportunity(paxg, Opportunity(OppParams()), capital=10000.0, start=i0)
L.append("## 1. Live rules on PAXG alone (1% risk per trade, all capital available)")
L.append(f"  trades {len(res.trades)}, win rate {res.win_rate:.0%}, profit factor {res.profit_factor:.2f}, "
         f"return {res.total_return:+.1%}, max drawdown {res.max_drawdown:.1%}")
L.append(f"  buy & hold PAXG over the same window: {paxg[-1].close / paxg[i0].open - 1:+.1%}")
yrs = (paxg[-1].open_time - paxg[i0].open_time) / DAY / 365
L.append(f"  per year: strategy {(1 + res.total_return) ** (1 / yrs) - 1:+.1%}, buy & hold {(paxg[-1].close / paxg[i0].open) ** (1 / yrs) - 1:+.1%}\n")

# 3. as an extra symbol in the live book
base_curve, base_trades = run(start=START)
data['PAXGUSDT'] = paxg
for qs in rank_at:
    rank_at[qs] = ['PAXGUSDT'] + [s for s in rank_at[qs] if s != 'PAXGUSDT']
with_curve, with_trades = run(start=START, top=16)            # PAXG + the usual top 15
del data['PAXGUSDT']
b, w = stats(base_curve), stats(with_curve)
L.append("## 3. Whole book, same window: top 15 by volume vs top 15 + PAXG (5 slots, 1% risk)")
L.append(f"  without PAXG: {b['cagr']:+.1%}/yr  maxDD {b['dd']:.1%}  Sharpe {b['sharpe']:.2f}  trades {len(base_trades)}")
L.append(f"  with PAXG:    {w['cagr']:+.1%}/yr  maxDD {w['dd']:.1%}  Sharpe {w['sharpe']:.2f}  trades {len(with_trades)}")
pt = [x for x in with_trades if x['sym'] == 'PAXGUSDT']
if pt:
    L.append(f"  PAXG trades inside the book: {len(pt)}, total {sum(x['r'] for x in pt):+.1f}R, "
             f"win {sum(x['r'] > 0 for x in pt) / len(pt):.0%}")
by, wy = by_year(base_curve), by_year(with_curve)
L.append("  year   without   with PAXG")
for y in by:
    L.append(f"  {y}   {by[y]:+7.1%}   {wy[y]:+7.1%}")

# 2. correlation
pmap = {c.open_time: c.close for c in paxg}
btc = {c.open_time: c.close for c in data['BTCUSDT']}
days = sorted(t for t in pmap if t in btc and t >= START)
pr = [pmap[days[i]] / pmap[days[i - 1]] - 1 for i in range(1, len(days))]
br = [btc[days[i]] / btc[days[i - 1]] - 1 for i in range(1, len(days))]
bm = dict(base_curve)
bd = [t for t in days if t in bm]
botr = [bm[bd[i]] / bm[bd[i - 1]] - 1 for i in range(1, len(bd))]
pr2 = [pmap[bd[i]] / pmap[bd[i - 1]] - 1 for i in range(1, len(bd))]
L.append("\n## 2. Is gold different?")
L.append(f"  correlation of daily returns: PAXG vs BTC {corr(pr, br):+.2f}, PAXG vs the bot {corr(pr2, botr):+.2f}")
worst = sorted(range(len(br)), key=lambda i: br[i])[:20]
L.append(f"  on BTC's 20 worst days (avg {sum(br[i] for i in worst) / 20:+.1%}), PAXG averaged {sum(pr[i] for i in worst) / 20:+.2%}")

# 4. gold sleeve: run the rules on PAXG with a fixed share of capital alongside the crypto book
L.append("\n## 4. Separate gold sleeve: X% of capital in the PAXG-only strategy, rest in the crypto book (daily rebalanced)")
# the single-coin backtest records one equity value per candle from i0 on
gmap = dict(zip([c.open_time for c in paxg[i0:]], res.equity))
common = [t for t in bd if t in gmap]
for wgt in (0.0, 0.2, 0.3, 0.5):
    eq, cv = 10000.0, [(common[0], 10000.0)]
    for tp, t in zip(common, common[1:]):
        eq *= 1 + wgt * (gmap[t] / gmap[tp] - 1) + (1 - wgt) * (bm[t] / bm[tp] - 1); cv.append((t, eq))
    s = stats(cv)
    L.append(f"  {wgt:.0%} gold sleeve: {s['cagr']:+.1%}/yr  maxDD {s['dd']:.1%}  Sharpe {s['sharpe']:.2f}")
print("\n".join(L))
