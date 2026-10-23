"""Research round 13: funding-rate carry (cash-and-carry), a market-neutral opportunity.

Perpetual futures pay a funding rate every 8 hours. When it is positive,
shorts are paid by longs. Buying the coin on spot and shorting the same
amount on the perpetual cancels the price risk and collects that payment.
This is a different source of profit from the trend bot: it does not need
the price to go anywhere.

Rules tested (daily, decided at the close, filled at that close):
  - for each coin, the trailing 7-day average funding, annualised
  - enter a hedge when it is above ENTER, exit when it falls below EXIT
  - at most K hedges at once, highest funding first, equal capital slots
  - each slot holds spot worth N and a short perp worth N with N/LEV margin,
    so a slot of capital C carries N = C / (1 + 1/LEV)
  - daily P&L = funding received + (spot move - perp move) on the hedge
    (the basis), minus costs: spot 0.10% + perp 0.05% taker, plus 0.05%
    slippage on each leg, on entry and on exit (0.50% round trip)

Data: Binance's public data dumps (data.binance.vision), monthly funding-rate
files and USDT-M perpetual daily klines; spot daily candles from
research/data/daily_long.pkl. Cached in research/data/funding.pkl.

Tuned on 2020-2023, tested on 2024 onward. Survivorship: only coins still
listed today are in the pool (LUNA, FTT etc. are missing), which matters less
here than for a directional strategy because the hedge has no price exposure,
but a collapse can still blow out the basis or the short's margin.
"""
import csv
import io
import itertools
import math
import os as _os
import pickle
import sys
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
DATA = _os.path.join(HERE, '..', 'data')
sys.path.insert(0, ROOT)

COINS = "BTC ETH BNB XRP ADA DOGE SOL TRX LTC BCH LINK DOT AVAX XLM ATOM ETC UNI NEAR FIL AAVE".split()
MONTHS = [f"{y}-{m:02d}" for y in range(2020, 2027) for m in range(1, 13) if f"{y}-{m:02d}" <= "2026-09"]
DAY = 86_400_000
d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m-%d')


def _rows(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            z = zipfile.ZipFile(io.BytesIO(r.read()))
    except Exception:
        return []
    out = []
    for row in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))):
        try:
            out.append([float(x) for x in row[:6]])
        except ValueError:
            pass   # header line (newer files have one, older don't)
    return out


def fetch_all():
    base = "https://data.binance.vision/data/futures/um/monthly"
    jobs = [(c, m, k) for c in COINS for m in MONTHS for k in ("funding", "kline")]

    def get(job):
        c, m, k = job
        if k == "funding":
            return job, _rows(f"{base}/fundingRate/{c}USDT/{c}USDT-fundingRate-{m}.zip")
        return job, _rows(f"{base}/klines/{c}USDT/1d/{c}USDT-1d-{m}.zip")

    out = {c: {"funding": {}, "perp": {}} for c in COINS}
    with ThreadPoolExecutor(16) as ex:
        for (c, m, k), rows in ex.map(get, jobs):
            for r in rows:
                if k == "funding":   # calc_time, interval_hours, rate
                    day = int(r[0]) // DAY * DAY
                    out[c]["funding"][day] = out[c]["funding"].get(day, 0.0) + r[2]
                else:                # open_time, open, high, low, close, ...
                    out[c]["perp"][int(r[0]) // DAY * DAY] = r[4]
    return out


cache = _os.path.join(DATA, 'funding.pkl')
if _os.path.exists(cache):
    fut = pickle.load(open(cache, 'rb'))
else:
    fut = fetch_all()
    pickle.dump(fut, open(cache, 'wb'))
spot_raw = pickle.load(open(_os.path.join(DATA, 'daily_long.pkl'), 'rb'))
spot = {c: {cs.open_time // DAY * DAY: cs.close for cs in spot_raw[c + 'USDT']} for c in COINS if c + 'USDT' in spot_raw}

# aligned daily panel: coin -> day -> (spot close, perp close, funding paid that day)
panel = {}
for c in COINS:
    if c not in spot:
        continue
    days = sorted(set(spot[c]) & set(fut[c]["perp"]) & set(fut[c]["funding"]))
    panel[c] = {t: (spot[c][t], fut[c]["perp"][t], fut[c]["funding"][t]) for t in days}
DAYS = sorted(set().union(*[set(p) for p in panel.values()]))
print(f"coins with data: {len(panel)}  days: {d(DAYS[0])} -> {d(DAYS[-1])}")
for c in panel:
    ts = sorted(panel[c])
    print(f"  {c:5s} {d(ts[0])} -> {d(ts[-1])}  avg funding {sum(panel[c][t][2] for t in ts) / len(ts) * 365:+.1%}/yr")

COST = 0.0025   # per side, both legs: (0.10% + 0.05%) spot + (0.05% + 0.05%) perp


def trailing(c, t, n=7):
    vals = [panel[c][t - i * DAY][2] for i in range(n) if (t - i * DAY) in panel[c]]
    return sum(vals) / len(vals) * 365 if len(vals) == n else None


def run(enter, exit_, k=5, lev=1.0, start=None, end=None, cost=COST, coins=None):
    coins = coins or list(panel)
    days = [t for t in DAYS if (start is None or t >= start) and (end is None or t < end)]
    equity, held, curve, n_trades, fund_total, basis_total, cost_total = 1.0, {}, [], 0, 0.0, 0.0, 0.0
    for i, t in enumerate(days):
        # 1. mark yesterday's hedges to today: funding + basis
        for c, h in list(held.items()):
            row = panel[c].get(t)
            if row is None:
                continue
            s, p, f = row
            fund = h["qty"] * p * f
            basis = h["qty"] * ((s - h["s"]) - (p - h["p"]))
            equity += fund + basis
            fund_total += fund; basis_total += basis
            h["s"], h["p"] = s, p
        # 2. exits
        for c in list(held):
            tr = trailing(c, t)
            if tr is None or tr < exit_ or t == days[-1]:
                h = held.pop(c)
                fee = h["qty"] * panel[c][t][0] * cost if t in panel[c] else h["N"] * cost
                equity -= fee; cost_total += fee
        # 3. entries, highest funding first
        if t != days[-1]:
            cands = sorted(((trailing(c, t), c) for c in coins if c not in held and t in panel[c]),
                           key=lambda x: -(x[0] or -9))
            for tr, c in cands:
                if tr is None or tr < enter or len(held) >= k:
                    break
                N = equity / k / (1 + 1 / lev)
                s, p, _ = panel[c][t]
                held[c] = {"qty": N / s, "s": s, "p": p, "N": N}
                fee = N * cost
                equity -= fee; cost_total += fee; n_trades += 1
        curve.append((t, equity, len(held)))
    return stats(curve, n_trades, fund_total, basis_total, cost_total)


def stats(curve, n, fund, basis, cost):
    eq = [e for _, e, _ in curve]
    yrs = (curve[-1][0] - curve[0][0]) / DAY / 365
    cagr = eq[-1] ** (1 / yrs) - 1 if yrs > 0 else 0
    peak, mdd = 1.0, 0.0
    for e in eq:
        peak = max(peak, e); mdd = max(mdd, 1 - e / peak)
    rets = [eq[i] / eq[i - 1] - 1 for i in range(1, len(eq))]
    mu = sum(rets) / len(rets); sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / len(rets)) or 1e-12
    used = sum(h for _, _, h in curve) / len(curve)
    by_year = {}
    for t, e, _ in curve:
        by_year.setdefault(d(t)[:4], [e, e])[1] = e
    return {"cagr": cagr, "total": eq[-1] - 1, "mdd": mdd, "sharpe": mu / sd * math.sqrt(365), "trades": n,
            "fund": fund, "basis": basis, "cost": cost, "avg_held": used, "worst_day": min(rets),
            "years": {y: b / a - 1 for y, (a, b) in by_year.items()}, "curve": curve}


def line(name, r):
    return (f"{name:34s} CAGR {r['cagr']:+6.1%}  total {r['total']:+7.1%}  maxDD {r['mdd']:5.1%}  "
            f"Sharpe {r['sharpe']:5.2f}  trades {r['trades']:4d}  avg held {r['avg_held']:.1f}  "
            f"funding {r['fund']:+.3f} basis {r['basis']:+.3f} costs {-r['cost']:+.3f}  worst day {r['worst_day']:+.2%}")


SPLIT = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
START = int(datetime(2020, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)

print("\n== 1. Tuning grid on 2020-03 .. 2023-12 (1x margin, max 5 hedges) ==")
grid = []
for enter, exit_ in itertools.product([0.05, 0.10, 0.15, 0.20, 0.30], [0.0, 0.03, 0.05, 0.10]):
    if exit_ >= enter:
        continue
    r = run(enter, exit_, start=START, end=SPLIT)
    grid.append((r["sharpe"], enter, exit_, r))
    print(line(f"enter {enter:.0%} exit {exit_:.0%}", r))
grid.sort(key=lambda x: -x[0])
_, BE, BX, _ = grid[0]
print(f"\nbest on training data by Sharpe: enter {BE:.0%}, exit {BX:.0%}")

print("\n== 2. Unseen data 2024-01 .. end ==")
print(line(f"tuned  enter {BE:.0%} exit {BX:.0%}", run(BE, BX, start=SPLIT)))
for enter, exit_ in [(0.10, 0.03), (0.15, 0.05), (0.20, 0.05)]:
    print(line(f"fixed  enter {enter:.0%} exit {exit_:.0%}", run(enter, exit_, start=SPLIT)))
print(line("always on BTC+ETH (enter -inf)", run(-9, -10, k=2, start=SPLIT, coins=["BTC", "ETH"])))

print("\n== 3. Whole period, by year (tuned rule) ==")
full = run(BE, BX, start=START)
print(line("full period", full))
for y, r in full["years"].items():
    print(f"   {y}  {r:+6.1%}")

print("\n== 4. Cost stress and margin (unseen data) ==")
for c in (0.0015, 0.0025, 0.004, 0.006):
    print(line(f"cost {c * 2:.2%} round trip", run(BE, BX, start=SPLIT, cost=c)))
for lev in (1.0, 2.0, 3.0):
    print(line(f"perp margin {lev:.0f}x", run(BE, BX, start=SPLIT, lev=lev)))
for k in (1, 3, 5, 10):
    print(line(f"max {k} hedges", run(BE, BX, start=SPLIT, k=k)))

print("\n== 5. Recent months (what the opportunity looks like now) ==")
recent = [t for t in DAYS if t >= DAYS[-1] - 90 * DAY]
for c in panel:
    vals = [panel[c][t][2] for t in recent if t in panel[c]]
    if vals:
        print(f"  {c:5s} last 90 days avg funding {sum(vals) / len(vals) * 365:+6.1%}/yr   last 7 days {trailing(c, max(t for t in recent if t in panel[c])) or 0:+6.1%}/yr")
r90 = run(BE, BX, start=DAYS[-1] - 90 * DAY)
print(line("tuned rule, last 90 days", r90))
