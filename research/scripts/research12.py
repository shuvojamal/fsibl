"""Research round 12: stress test on 8+ years of history, Monte Carlo, full metrics.

The final rules (top 15 by trailing-90-day volume, 5 of 8 checks, RSI 40-80,
2xATR initial stop, 3xATR trailing stop, 1% risk, max 5 open, highest score
first, stops acted on at the daily close) on daily candles from August 2017,
covering the 2018 crash, the March 2020 crash, LUNA and FTX in 2022.

Outputs: per-year and per-regime results, expectancy in R, Sharpe/Sortino/
Calmar, cost stress, an ADX "trend present" filter test, and a Monte Carlo
resampling of the trade sequence for the distribution of drawdowns and
yearly returns.

Known limitation: coins delisted from Binance (LUNA, FTT and others) cannot
be downloaded, so the pool still leans towards survivors. The volume rule
limits the damage (dead coins fall out of the top 15 before they die), but
does not remove it.
"""
import math
import os as _os
import pickle
import random
import sys
import time
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')
RES = _os.path.join(HERE, '..', 'results')
sys.path.insert(0, ROOT)
from datetime import datetime, timezone
from tradebot.backtest import FEE, SLIPPAGE
from tradebot.data import fetch_candles
from tradebot.indicators import ema
from tradebot.opportunity import Opportunity, OppParams

d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m-%d')
POOL = ("BTC ETH BNB XRP ADA DOGE SOL TRX LTC BCH LINK DOT AVAX XLM ATOM ETC UNI NEAR FIL AAVE ALGO "
        "EOS NEO IOTA DASH ZEC XMR QTUM ICX VET WAVES OMG ONT ZIL BAT THETA MATIC FTM SAND MANA AXS "
        "SHIB PEPE SUI ARB OP APT INJ HBAR ICP GRT CRV RUNE LUNA FTT").split()
cache = _os.path.join(OUT, 'daily_long.pkl')
if _os.path.exists(cache):
    data = pickle.load(open(cache, 'rb'))
else:
    data, missing = {}, []
    for b in POOL:
        try:
            cs = fetch_candles(b + 'USDT', '1d', 3400)
            if len(cs) >= 260:
                data[b + 'USDT'] = cs
            else:
                missing.append(b)
        except Exception:
            missing.append(b)
        time.sleep(0.25)
    print('could not download (delisted or too short):', ' '.join(missing))
    pickle.dump(data, open(cache, 'wb'))

QUARTER = 90 * 86_400_000
t0 = min(cs[0].open_time for cs in data.values())
tN = max(cs[-1].open_time for cs in data.values())
quarters = list(range(t0, tN + QUARTER, QUARTER))
rank_at = {}
for qs in quarters:
    vols = {s: sum(c.volume * c.close for c in cs if qs - QUARTER <= c.open_time < qs) for s, cs in data.items()}
    rank_at[qs] = sorted((s for s in vols if vols[s] > 0), key=vols.get, reverse=True)
btc = data['BTCUSDT']; be = ema([c.close for c in btc], 200)
btc_bull = {c.open_time: (be[i] is not None and c.close > be[i]) for i, c in enumerate(btc)}


class ADXFiltered(Opportunity):
    """Also require ADX(14) > threshold: only trade when a trend is actually present."""
    def __init__(self, p, threshold=20):
        super().__init__(p); self.threshold = threshold
    def prepare(self, candles):
        super().prepare(candles)
        h = [c.high for c in candles]; l = [c.low for c in candles]; c = self.closes
        n = 14; self.adx = [None] * len(c)
        pdm, ndm, tr = [0.0], [0.0], [h[0] - l[0]]
        for i in range(1, len(c)):
            up, dn = h[i] - h[i - 1], l[i - 1] - l[i]
            pdm.append(up if up > dn and up > 0 else 0.0); ndm.append(dn if dn > up and dn > 0 else 0.0)
            tr.append(max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])))
        sp = sn = st = 0.0; dxs = []
        for i in range(1, len(c)):
            sp = sp - sp / n + pdm[i]; sn = sn - sn / n + ndm[i]; st = st - st / n + tr[i]
            if i < n or st == 0:
                continue
            pdi, ndi = 100 * sp / st, 100 * sn / st
            dxs.append(100 * abs(pdi - ndi) / (pdi + ndi) if pdi + ndi else 0)
            if len(dxs) >= n:
                self.adx[i] = sum(dxs[-n:]) / n
        return self
    def signal(self, i):
        if self.adx[i] is None or self.adx[i] < self.threshold:
            return None
        return super().signal(i)


def run(make=lambda: Opportunity(OppParams()), top=15, fee=FEE, slip=SLIPPAGE, max_open=5, risk=0.01,
        capital=10000.0, start=None, end=None):
    strats = {s: make().prepare(cs) for s, cs in data.items()}
    idx = {s: {c.open_time: i for i, c in enumerate(cs)} for s, cs in data.items()}
    times = sorted(set(t for s in data for t in idx[s]))
    times = [t for t in times if (start is None or t >= start) and (end is None or t < end)]
    cash, pos, pending, curve, trades = capital, {}, {}, [], []
    eq_of = lambda t: cash + sum(q['qty'] * data[k][idx[k][t]].close for k, q in pos.items() if t in idx[k])
    for t in times:
        eq_now = curve[-1][1] if curve else capital
        for s in [s for s, (a, _) in pending.items() if a == 'sell']:
            i = idx[s].get(t)
            if i is None or s not in pos:
                continue
            px = data[s][i].open * (1 - slip); q = pos.pop(s)
            p = q['qty'] * px * (1 - fee) - q['cost']; cash += q['qty'] * px * (1 - fee)
            trades.append(dict(t=t, pnl=p, r=p / q['risk'], sym=s, bull=q['bull']))
        buys = sorted([(s, p) for s, (a, p) in pending.items() if a == 'buy'], key=lambda x: -x[1].score)
        for s, plan in buys:
            i = idx[s].get(t)
            if i is None or s in pos or len(pos) >= max_open:
                continue
            entry = data[s][i].open * (1 + slip)
            if entry <= plan.stop:
                continue
            qty = min(eq_now * risk / (entry - plan.stop), cash * (1 - fee) / entry)
            if qty > 0:
                cash -= qty * entry / (1 - fee)
                pos[s] = dict(qty=qty, cost=qty * entry / (1 - fee), stop=plan.stop, peak=entry,
                              risk=qty * (entry - plan.stop), bull=btc_bull.get(t, False))
        pending = {}
        qs = quarters[max(0, min(len(quarters) - 1, (t - t0) // QUARTER))]
        allowed = set(rank_at[qs][:top])
        for s, cs in data.items():
            i = idx[s].get(t)
            if i is None:
                continue
            c, st = cs[i], strats[s]
            if s in pos:
                q = pos[s]
                if c.low <= q['stop']:            # acted on at the daily close (live behaviour)
                    pending[s] = ('sell', None); continue
                st.peak = max(q['peak'], c.close); q['peak'] = st.peak
                q['stop'] = st.update_stop(i, q['stop'])
            elif s in allowed:
                plan = st.signal(i)
                if plan:
                    pending[s] = ('buy', plan)
        curve.append((t, eq_of(t)))
    return curve, trades


def metrics(curve, trades, capital=10000.0):
    eq = [e for _, e in curve]
    rets = [eq[i] / eq[i - 1] - 1 for i in range(1, len(eq))]
    years = len(eq) / 365
    pk = dd = 0
    for e in eq:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    mu = sum(rets) / len(rets); sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / len(rets))
    down = math.sqrt(sum(min(r, 0) ** 2 for r in rets) / len(rets))
    cagr = (eq[-1] / capital) ** (1 / years) - 1
    rs = [x['r'] for x in trades]
    wins = [x for x in rs if x > 0]; losses = [x for x in rs if x <= 0]
    return dict(ret=eq[-1] / capital - 1, cagr=cagr, dd=dd, sharpe=mu / sd * math.sqrt(365) if sd else 0,
                sortino=mu / down * math.sqrt(365) if down else 0, calmar=cagr / -dd if dd else 0,
                n=len(rs), win=len(wins) / len(rs) if rs else 0, exp_r=sum(rs) / len(rs) if rs else 0,
                avg_win=sum(wins) / len(wins) if wins else 0, avg_loss=sum(losses) / len(losses) if losses else 0,
                pf=sum(wins) / -sum(losses) if losses else 99, best=max(rs) if rs else 0, years=years)


def fmt(m):
    return (f"{m['ret']:+8.1%} total, {m['cagr']:+6.1%}/yr, maxDD {m['dd']:6.1%}, Sharpe {m['sharpe']:4.2f}, "
            f"Sortino {m['sortino']:4.2f}, Calmar {m['calmar']:4.2f}, {m['n']} trades, win {m['win']:4.0%}, "
            f"expectancy {m['exp_r']:+.2f}R (avg win {m['avg_win']:+.2f}R, avg loss {m['avg_loss']:+.2f}R, best {m['best']:+.1f}R), PF {m['pf']:4.2f}")


L = []
L.append(f"Pool: {len(data)} coins downloaded ({', '.join(s[:-4] for s in data)}).")
L.append(f"History: {d(t0)} -> {d(tN)}. Top 15 by trailing-90d volume, quarterly; max 5 open; 1% risk; "
         f"stops acted on at the daily close.\n")
curve, trades = run()
m = metrics(curve, trades)
L.append("## Whole period\n" + fmt(m))
eqs = [e for _, e in curve]
L.append(f"Buy & hold BTC over the same period: {btc[-1].close / btc[next(i for i, c in enumerate(btc) if c.open_time >= curve[0][0])].open - 1:+.1%}")

L.append("\n## By calendar year (equity at year end vs start)")
years = sorted(set(datetime.fromtimestamp(t / 1000, timezone.utc).year for t, _ in curve))
for y in years:
    pts = [(t, e) for t, e in curve if datetime.fromtimestamp(t / 1000, timezone.utc).year == y]
    pk = dd = 0
    for _, e in pts:
        pk = max(pk, e); dd = min(dd, e / pk - 1)
    bi = [c for c in btc if datetime.fromtimestamp(c.open_time / 1000, timezone.utc).year == y]
    ny = sum(1 for x in trades if datetime.fromtimestamp(x['t'] / 1000, timezone.utc).year == y)
    L.append(f"  {y}: {pts[-1][1] / pts[0][1] - 1:+7.1%}  (worst drop in year {dd:6.1%}, {ny:3} trades)   BTC {bi[-1].close / bi[0].open - 1:+7.1%}")

L.append("\n## By market regime at entry (BTC above / below its 200-day EMA)")
for label, flag in (("BTC above 200-EMA", True), ("BTC below 200-EMA", False)):
    rs = [x['r'] for x in trades if x['bull'] == flag]
    if rs:
        L.append(f"  {label}: {len(rs)} trades, win {sum(r > 0 for r in rs) / len(rs):4.0%}, expectancy {sum(rs) / len(rs):+.2f}R, total {sum(rs):+.1f}R")

L.append("\n## Distribution of trade results (R = multiples of the amount risked)")
rs = sorted(x['r'] for x in trades)
for lo, hi in ((-99, -1.5), (-1.5, -0.5), (-0.5, 0), (0, 1), (1, 3), (3, 10), (10, 999)):
    k = sum(lo <= r < hi for r in rs)
    L.append(f"  {lo:>5} .. {hi:<4}R : {k:4} trades  {'#' * max(0, round(k / max(1, len(rs)) * 100))}")
top_share = sum(sorted((x['pnl'] for x in trades), reverse=True)[:max(1, len(trades) // 10)]) / max(1e-9, sum(x['pnl'] for x in trades))
L.append(f"  Share of total profit from the best 10% of trades: {top_share:.0%}")

L.append("\n## Stress and variants (whole period)")
for label, kw in (("costs x2 (fee 0.2%, slip 0.1%)", dict(fee=0.002, slip=0.001)),
                  ("costs x3", dict(fee=0.003, slip=0.0015)),
                  ("risk 0.5% per trade", dict(risk=0.005)),
                  ("risk 2% per trade", dict(risk=0.02)),
                  ("top 10 instead of 15", dict(top=10)),
                  ("ADX(14) > 20 required", dict(make=lambda: ADXFiltered(OppParams(), 20))),
                  ("ADX(14) > 25 required", dict(make=lambda: ADXFiltered(OppParams(), 25)))):
    c2, t2 = run(**kw)
    L.append(f"  {label:32} {fmt(metrics(c2, t2))}")

L.append("\n## Monte Carlo: 10,000 reshuffles of the actual trade sequence (R per trade, 1% risk compounding)")
random.seed(12)
R = [x['r'] for x in trades]
per_year = len(R) / m['years']
dds, yr1 = [], []
for _ in range(10000):
    seq = random.choices(R, k=len(R))      # bootstrap with replacement
    eq = pk = 1.0; worst = 0
    for k, r in enumerate(seq):
        eq *= 1 + 0.01 * r
        pk = max(pk, eq); worst = min(worst, eq / pk - 1)
        if k + 1 == int(per_year):
            yr1.append(eq - 1)
    dds.append(worst)
dds.sort(); yr1.sort()
q = lambda v, p: v[int(p * (len(v) - 1))]
L.append(f"  {len(R)} trades, about {per_year:.0f} a year. (Sequential, so it ignores overlap between open positions;")
L.append("  use it for the shape of the risk, not the exact level.)")
L.append(f"  Max drawdown over the full history: median {q(dds, .5):.1%}, 1-in-20 worst {q(dds, .05):.1%}, 1-in-100 worst {q(dds, .01):.1%}")
L.append(f"  First-year return: median {q(yr1, .5):+.1%}, 1-in-20 worst {q(yr1, .05):+.1%}, 1-in-20 best {q(yr1, .95):+.1%}")
L.append(f"  Chance the first year loses money: {sum(x < 0 for x in yr1) / len(yr1):.0%}")
out = "\n".join(L) + "\n"
open(_os.path.join(RES, 'research12.out'), 'w').write(out)
print(out)
