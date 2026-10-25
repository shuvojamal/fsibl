"""Research round 38: do the bot's rules work on Dhaka Stock Exchange shares?

The owner asked for a DSE option: signals only (buy, sell, trailing stop),
orders placed by hand. Before building it, test whether the same rules make
money on DSE at all.

Data: "Dhaka Stock Exchange End-of-Day Financial Dataset with Coverage
Metadata", Mendeley Data v4 (2026), doi:10.17632/23553sm4tn.4, CC BY 4.0;
the corporate-action ADJUSTED daily prices (bonus shares would otherwise
look like crashes and trip stops). 395 equities plus the DSEX index,
2012-10 .. 2026-01; spot-checked against dse.com.bd's own day-end archive
(identical). Cached compactly in research/data/dse_daily_adj.pkl.gz
(equities and DSEX only, float32).

Method: round 12's simulator unchanged (daily close signals, next-open
fills, 2xATR stop, 3xATR trail, stops acted on at the close, top-N by
trailing-90-day traded value re-ranked quarterly), with DSE costs: 0.40%
brokerage and charges plus 0.30% slippage per side (DSE shares are far less
liquid than crypto). Days a share did not trade are absent from the data,
so orders wait for the next day it trades (as with DSE's floor-price
freezes). Halves: 2013-10 .. 2019-12 and 2020-01 .. 2026-01.
Benchmark: buying the DSEX index (a price index; dividends of roughly 3-5%
a year are not included, which flatters the bot a little).

Primary set-up, chosen before running: 8 slots x 1% risk, 6 of 8 checks,
top 20. Variants shown for robustness: 0.5% risk, 5 checks, top 10/30,
and a cost stress (0.6% + 0.5% per side).

Pass bar, decided before running: DSE signals are worth offering if the
primary set-up (a) makes money after costs in BOTH halves, (b) has a higher
Sharpe than holding DSEX in both halves, and (c) has a shallower worst drop
than DSEX in both halves.
"""
import csv
import gzip
import io
import os as _os
import pickle
import sys
import zipfile
from array import array
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
sys.path.insert(0, ROOT)
from tradebot.data import Candle
from tradebot.opportunity import Opportunity, OppParams

DAY = 86_400_000
CACHE = _os.path.join(ROOT, 'research', 'data', 'dse_daily_adj.pkl.gz')
ZIP = _os.environ.get("DSE_ZIP", "")   # the Mendeley zip, only needed to build the cache


def build():
    z = zipfile.ZipFile(ZIP)
    root = "Dhaka Stock Exchange End-of-Day Financial Dataset/"
    meta = list(csv.DictReader(io.TextIOWrapper(z.open(root + "metadata/company_metadata.csv"))))
    keep = {m["Ticker"] for m in meta if m["Instrument_Type"] == "Equity"} | {"00DSEX"}
    out = {}
    for t in sorted(keep):
        try:
            rows = list(csv.DictReader(io.TextIOWrapper(z.open(root + f"Company Separated Adjusted Data/{t}.csv"))))
        except KeyError:
            continue
        rows = [r for r in rows if float(r["Close"]) > 0 and float(r["Open"]) > 0]
        if len(rows) < 260:
            continue
        ts = array('q', [int(datetime.strptime(r["Date"], "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000) for r in rows])
        vals = array('f', [float(r[k]) for r in rows for k in ("Open", "High", "Low", "Close", "Volume")])
        out[t] = (ts, vals)
    with gzip.open(CACHE, "wb") as f:
        pickle.dump(out, f)
    return out


def unpack(packed):
    return {s: [Candle(t, float(v[5 * i]), float(v[5 * i + 1]), float(v[5 * i + 2]), float(v[5 * i + 3]), float(v[5 * i + 4]), t + DAY - 1)
                for i, t in enumerate(ts)] for s, (ts, v) in packed.items()}


raw = pickle.load(gzip.open(CACHE)) if _os.path.exists(CACHE) else build()
data = unpack(raw)
dsex = data.pop("00DSEX")

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
head = head.replace("btc = data['BTCUSDT']", "btc = BENCH")
pk = _os.path.join(ROOT, 'research', 'data', '_r38_tmp.pkl')
pickle.dump(data, open(pk, 'wb'))
ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r38b', 'BENCH': dsex}
exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
_os.remove(pk)
run, metrics = ns['run'], ns['metrics']

ms = lambda y, m, d: int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)
HALVES = [("2013-10..2019", ms(2013, 10, 1), ms(2020, 1, 1)), ("2020..2026-01", ms(2020, 1, 1), None)]
FEE, SLIP = 0.004, 0.003


def bench(s, e):
    cs = [c for c in dsex if c.open_time >= s and (e is None or c.open_time < e)]
    curve = [(c.open_time, 10000.0 * c.close / cs[0].open) for c in cs]
    return metrics(curve, [])


CASES = [
    ("PRIMARY 8x1%, 6 chk, top 20", dict(risk=0.01, ms=6, top=20)),
    ("8x0.5%, 6 chk, top 20", dict(risk=0.005, ms=6, top=20)),
    ("8x1%, 5 chk, top 20", dict(risk=0.01, ms=5, top=20)),
    ("8x1%, 6 chk, top 10", dict(risk=0.01, ms=6, top=10)),
    ("8x1%, 6 chk, top 30", dict(risk=0.01, ms=6, top=30)),
    ("PRIMARY, costs 0.6%+0.5%", dict(risk=0.01, ms=6, top=20, fee=0.006, slip=0.005)),
]
L = [f"DSE: {len(data)} equities with 260+ days, adjusted prices 2012-10 .. 2026-01; costs {FEE:.2%} + {SLIP:.2%} slippage per side\n",
     f"{'case':30s} | " + " | ".join(f"{h:^44s}" for h, _, _ in HALVES),
     f"{'':30s} | " + " | ".join(f"{'ret/yr':>8s} {'Sharpe':>6s} {'maxDD':>7s} {'trades':>6s} {'win':>4s} {'avgR':>5s}" for _ in HALVES)]
res = {}
for name, c in CASES:
    row = f"{name:30s} |"
    for h, s, e in HALVES:
        m = metrics(*run(make=lambda ms_=c['ms']: Opportunity(OppParams(min_score=ms_)), top=c['top'], max_open=8, risk=c['risk'],
                         fee=c.get('fee', FEE), slip=c.get('slip', SLIP), start=s, end=e))
        res[(name, h)] = m
        row += f" {m['cagr']:+8.1%} {m['sharpe']:6.2f} {m['dd']:7.1%} {m['n']:6d} {m['win']:4.0%} {m['exp_r']:+5.2f} |"
    L.append(row)
row = f"{'hold DSEX (price index)':30s} |"
for h, s, e in HALVES:
    m = bench(s, e); res[("DSEX", h)] = m
    row += f" {m['cagr']:+8.1%} {m['sharpe']:6.2f} {m['dd']:7.1%} {'':6s} {'':4s} {'':5s} |"
L.append(row)
P = CASES[0][0]
checks = [(f"makes money after costs, {h}", res[(P, h)]['cagr'] > 0) for h, _, _ in HALVES]
checks += [(f"Sharpe above DSEX, {h}", res[(P, h)]['sharpe'] > res[("DSEX", h)]['sharpe']) for h, _, _ in HALVES]
checks += [(f"shallower worst drop than DSEX, {h}", res[(P, h)]['dd'] > res[("DSEX", h)]['dd']) for h, _, _ in HALVES]
L += [""] + [f"  {'PASS' if ok else 'FAIL'}  {t}" for t, ok in checks]
L.append(f"\nverdict: {'PASS: worth offering DSE signals' if all(ok for _, ok in checks) else 'FAIL: not worth offering as is'}")

# Diagnostics, added after the verdict (they cannot change it): is there any edge
# before costs, and do wider stops (costs become a smaller share of the risk) help?
DIAG = [("no costs at all (gross edge)", dict(fee=0.0, slip=0.0)),
        ("stops 4xATR, trail 6xATR", dict(stop=4.0, trail=6.0)),
        ("stops 4xATR, trail 6xATR, no costs", dict(stop=4.0, trail=6.0, fee=0.0, slip=0.0))]
L += ["", "Diagnostics on the primary set-up (not part of the pass bar):"]
for name, c in DIAG:
    row = f"{name:36s} |"
    for h, s, e in HALVES:
        m = metrics(*run(make=lambda c=c: Opportunity(OppParams(min_score=6, stop_atr=c.get('stop', 2.0), trail_atr=c.get('trail', 3.0))),
                         top=20, max_open=8, risk=0.01, fee=c.get('fee', FEE), slip=c.get('slip', SLIP), start=s, end=e))
        row += f" {h} {m['cagr']:+7.1%} Sh {m['sharpe']:5.2f} DD {m['dd']:6.1%} avgR {m['exp_r']:+5.2f} |"
    L.append(row)
print("\n".join(L))
