"""Research round 39: can the 1999-2025 DSE dataset extend round 38's test back to 1999?

The owner pointed to "Dhaka Stock Exchange Historical Data (1999-2025)",
Mendeley Data (doi:10.17632/5mww8rb9td.1, CC BY 4.0): 531 instruments,
1999-01 .. 2025-04, daily OHLCV. It is NOT adjusted for bonus shares (ACI
drops 147.8 -> 127.0 on its 2024-11-18 bonus), and unadjusted prices make
every bonus look like a crash and trip stops. The extra 1999-2012 years
(the 2010 bubble and crash) would be a valuable out-of-sample test for
round 38 if the data could be adjusted.

Test: detect corporate actions from the data itself (a record-date row with
open = 0 and volume = 0, then a drop of more than 5%) and check that rule
against the true adjustments known from round 38's adjusted dataset for
2012-11 .. 2025-04. Pass bar, decided before running: usable if it finds at
least 90% of real events with few false alarms. Paths: set D and M below to
the two unzipped datasets (not cached in the repo; this round uses no
price data beyond the check).
"""
import csv, os, statistics, collections
D = __import__("os").environ.get("DSE_1999", "m2/Dhaka Stock Exchange Historical Data (1999-2025)/Instrument_Based")
M = __import__("os").environ.get("DSE_ADJ", "mendeley/Dhaka Stock Exchange End-of-Day Financial Dataset")
def fl(x):
    try: return float(x)
    except ValueError: return 0.0
def load(p): return [{**r, **{k: fl(r[k]) for k in ("Open","High","Low","Close","Volume") if k in r}} for r in sorted(csv.DictReader(open(p)), key=lambda r: r["Date"])]
def detect(rows):
    ev = {}
    for i in range(2, len(rows)):
        p, c, q = rows[i-1], rows[i], rows[i-2]
        if float(p['Volume']) == 0 and float(p['Open']) == 0 and float(c['Close']) > 0 and float(q['Close']) > 0:
            r = float(c['Close']) / float(p['Close'] or q['Close'])
            if r < 0.95: ev[c['Date']] = r
    return ev
tp = fp = fn = 0; errs = []
for f in sorted(os.listdir(M + "/Company Separated Adjusted Data")):
    if not os.path.exists(os.path.join(D, f)): continue
    a = {r['Date']: float(r['Close']) for r in load(f"{M}/Company Separated Adjusted Data/{f}")}
    u = {r['Date']: float(r['Close']) for r in load(f"{M}/Company Separated UnAdjusted Data/{f}")}
    ds = sorted(d for d in a if d in u and u[d] > 0 and '2012-11-01' <= d <= '2025-04-08')
    truth = {}
    for k in range(1, len(ds) - 3):
        r0, r1, r3 = a[ds[k-1]]/u[ds[k-1]], a[ds[k]]/u[ds[k]], a[ds[k+3]]/u[ds[k+3]]
        if abs(r1/r0 - 1) > 0.03 and abs(r3/r1 - 1) < 0.01:      # persistent change = real corporate action
            truth[ds[k]] = r0 / r1
    det = {d: r for d, r in detect(load(os.path.join(D, f))).items() if '2012-11-01' <= d <= '2025-04-08'}
    for d, r in truth.items():
        if r > 0.97: continue                                     # ignore tiny ones
        if d in det: tp += 1; errs.append(abs(det[d] / r - 1))
        else: fn += 1
    fp += sum(1 for d in det if d not in truth)
print(f"real events found {tp}, missed {fn}, false alarms {fp}; ratio error median {statistics.median(errs):.1%}, 90th pct {sorted(errs)[int(.9*len(errs))]:.1%}")
z = collections.Counter()
for f in os.listdir(D):
    for r in csv.DictReader(open(os.path.join(D, f))):
        if fl(r['Volume']) == 0 and fl(r['Open']) == 0: z[r['Date'][:4]] += 1
print("record-date style rows per year:", dict(sorted(z.items())))
