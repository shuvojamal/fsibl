"""Research round 42: the 30 DSE blue chips from a CFA's 25-year table, in our data.

The owner shared a LinkedIn post (Md Sajib Hossain, CFA, "Value creation and
market return of top 30 listed companies in DSE (2001-2025)") showing total
market returns of 2.2%-24.8% a year since 2001 or listing, counting cash
dividends, bonus shares, splits and rights subscriptions.

Questions: (1) what did the same 30 shares do in our data, 2013-01 .. 2026-01
(price + bonus only, no cash dividends)? (2) How did an equal-weight basket
of all 30 do against DSEX in round 38's two halves (yearly rebalancing,
0.7% costs per side)? The list was chosen in 2025 (today's blue chips),
so this is a hindsight basket, not a strategy test; no pass bar.
"""
import os as _os

HERE = _os.path.dirname(_os.path.abspath(__file__))
g = {'__file__': _os.path.join(HERE, 'research41.py'), '__name__': 'r42'}
src = open(_os.path.join(HERE, 'research41.py')).read()
exec(src[:src.index('\nHALVES = [')], g)
S, CAL, dsex, stats, ms, backtest, last_close = g['S'], g['CAL'], g['dsex'], g['stats'], g['ms'], g['backtest'], g['last_close']

# (ticker, the post's market return %/yr, base year)
POST = [("MARICO", 17.2, 2009), ("DUTCHBANGL", 20.4, 2003), ("BERGERPBL", 18.2, 2006), ("CITYBANK", 22.1, 2001),
        ("BRACBANK", 18.4, 2007), ("BATBC", 18.3, 2001), ("BSRMLTD", 8.0, 2015), ("PRIMEBANK", 14.6, 2001),
        ("IDLC", 15.7, 2001), ("PUBALIBANK", 20.6, 2001), ("OLYMPIC", 24.8, 2001), ("APEXFOOT", 15.0, 2001),
        ("GP", 7.4, 2009), ("DBH", 4.2, 2008), ("GREENDELT", 15.4, 2001), ("RELIANCINS", 17.8, 2001),
        ("RECKITTBEN", 18.0, 2001), ("EBL", 15.0, 2001), ("WALTONHIL", 8.5, 2020), ("BSCPLC", 10.7, 2012),
        ("BSC", 15.6, 2005), ("BATASHOE", 10.8, 2001), ("ACI", 13.5, 2001), ("LINDEBD", 13.5, 2001),
        ("UNILEVERCL", 17.3, 2002), ("BXPHARMA", 14.7, 2001), ("EASTRNLUB", 15.6, 2001), ("LHB", 11.1, 2003),
        ("MATINSPINN", 6.1, 2014), ("ENVOYTEX", 2.2, 2012)]

end_i = len(CAL) - 1
start_i = next(k for k, t in enumerate(CAL) if t >= ms(2013, 1, 22))
L = ["The post's 30 blue chips in our data (price + bonus, cash dividends NOT included)\n",
     f"{'share':11s} {'post: total/yr since base':>26s} {'ours: 2013-01..2026-01':>23s} {'gap (mostly dividends + earlier years)':>40s}"]
rows = []
for s, post, base in POST:
    d = S.get(s)
    if not d:
        L.append(f"{s:11s} {post:+25.1f}% {'not in data':>23s}"); continue
    first = next((k for k in range(start_i, end_i) if CAL[k] in d), None)
    c0, c1 = last_close(s, first), last_close(s, end_i)
    yrs = (CAL[end_i] - CAL[first]) / (365.25 * 86_400_000)
    ours = (c1 / c0) ** (1 / yrs) - 1
    rows.append(ours)
    L.append(f"{s:11s} {post:+25.1f}% {ours:+22.1%} {post / 100 - ours:+39.1%}")
L.append(f"\nmedian of ours: {sorted(rows)[len(rows) // 2]:+.1%}/yr; shares with a loss since 2013: {sum(r < 0 for r in rows)} of {len(rows)}")

HALVES = [("2013-10..2019", ms(2013, 10, 1), ms(2020, 1, 1)), ("2020..2026-01", ms(2020, 1, 1), None), ("2013-10..2026-01", ms(2013, 10, 1), None)]
L += ["", f"{'equal-weight basket, yearly rebalance':38s} | " + " | ".join(f"{h:^27s}" for h, _, _ in HALVES)]
for name, fn in (("30 blue chips (hindsight list)", lambda s, e: backtest(30, s, e, (1,), fixed=[p[0] for p in POST])),
                 ("hold DSEX (price index)", lambda s, e: [(t, dsex[t][1]) for t in CAL if t >= s and (e is None or t < e)])):
    row = f"{name:38s} |"
    for h, s, e in HALVES:
        m = stats(fn(s, e)); row += f" {m['cagr']:+7.1%} Sh {m['sharpe']:5.2f} DD {m['dd']:6.1%} |"
    L.append(row)
print("\n".join(L))
