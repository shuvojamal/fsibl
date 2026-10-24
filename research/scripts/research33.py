"""Research round 33: a closer look at the eight buy checks.

The owner asked for a deeper analysis of the buy signal. Round 7 did a
check-by-check ablation on one data set with 5 slots and 5 checks; the bot
now runs 8 slots and 6 of 8 checks (rounds 28-30), and round 21's six
close-time data sets let every answer be checked 12 times.

Part A - does the score mean anything? Every coin-day of the 30 coins
(six close times), grouped by score 0-8: how often it happens, and what the
live exit (buy next open, 2xATR stop, 3xATR trailing stop, sell next open
after a close below the stop) would have made from there, in R (multiples of
the initial risk) after costs. No portfolio limits, so each signal counts.

Part B - what does each check add? Among signal days (score >= 6), the
average R when the check passed vs when it failed (up to two may fail).

Part C - would the bot be better with a check removed (treated as always
passing) or made mandatory (no buy without it)? Round 12's simulator,
top 15, steady set-up (8 slots, 0.5% risk, 6 checks), 12 cells.

Pass bar for Part C, decided before running: a variant is recommended only
if it has the higher Sharpe than the live rules in at least 10 of 12 cells
(stricter than the usual 9 because 16 variants are tried at once) AND a
2022-26 median worst drop no more than 3 points deeper. Parts A and B are
descriptive; no change is made from them alone.
"""
import os as _os
import pickle
import statistics
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r33'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, simulate, OFFSETS, H = ns21['raw'], ns21['unpack'], ns21['simulate'], ns21['OFFSETS'], ns21['H']
from tradebot.backtest import FEE, SLIPPAGE
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
NAMES = ["trend_up", "ema_aligned", "momentum", "rsi_zone", "volume", "volatility_ok", "breakout", "pullback"]
half_of = lambda t, o: "2018-21" if t < SPLIT + o * H else "2022-26"


def trade_r(cs, st, i):
    """R multiple of the live exit for a signal on candle i (entry at the next open)."""
    if i + 1 >= len(cs):
        return None
    a = st.atr[i]
    entry = cs[i + 1].open * (1 + SLIPPAGE)
    stop = cs[i].close - 2 * a
    risk = entry - stop
    if risk <= 0:
        return None
    peak = cs[i].close
    for j in range(i + 1, len(cs)):
        if cs[j].low <= stop:
            if j + 1 >= len(cs):
                return None
            out = cs[j + 1].open * (1 - SLIPPAGE)
            return (out * (1 - FEE) - entry / (1 - FEE)) / risk
        peak = max(peak, cs[j].close)
        if st.atr[j] is not None:
            stop = max(stop, peak - 3 * st.atr[j])
    return None                                   # still open at the end of the data


# ---- Parts A and B ---------------------------------------------------------
by_score = {}                                     # (half, score) -> list of R
by_check = {}                                     # (half, name, passed) -> list of R
for o in OFFSETS:
    data = unpack(raw[o])
    for s, cs in data.items():
        st = Opportunity(OppParams()).prepare(cs)
        for i in range(len(cs)):
            if cs[i].open_time < START + o * H:
                continue
            ch = st.checks(i)
            if ch is None:
                continue
            score = sum(ok for _, ok in ch)
            if score < 4:                         # count only; R of weak days isn't needed
                by_score.setdefault((half_of(cs[i].open_time, o), score), []).append(None)
                continue
            r = trade_r(cs, st, i)
            if r is None:
                continue
            h = half_of(cs[i].open_time, o)
            by_score.setdefault((h, score), []).append(r)
            if score >= 6:
                for n, ok in ch:
                    by_check.setdefault((h, n, ok), []).append(r)

L = ["Part A - every coin-day by score (30 coins x six close times); R = live exit from that day, after costs\n",
     f"{'score':>5s} | {'days 18-21':>10s} {'avg R':>6s} {'win':>5s} | {'days 22-26':>10s} {'avg R':>6s} {'win':>5s} {'median R':>9s}"]
for sc in range(9):
    row = f"{sc:5d} |"
    for h in ("2018-21", "2022-26"):
        rs = by_score.get((h, sc), [])
        rr = [x for x in rs if x is not None]
        if rr:
            row += f" {len(rs):10d} {sum(rr) / len(rr):+6.2f} {sum(x > 0 for x in rr) / len(rr):5.0%} |"
        else:
            row += f" {len(rs):10d} {'':>6s} {'':>5s} |"
    rr = [x for x in by_score.get(("2022-26", sc), []) if x is not None]
    row += f" {statistics.median(rr):+9.2f}" if rr else ""
    L.append(row)

L += ["", "Part B - signal days (score >= 6): average R when each check passed vs failed",
      f"{'check':14s} | {'18-21 pass':>10s} {'fail':>6s} {'n fail':>7s} | {'22-26 pass':>10s} {'fail':>6s} {'n fail':>7s} | {'passes on':>9s}"]
for n in NAMES:
    row = f"{n:14s} |"
    tot = fail_n = 0
    for h in ("2018-21", "2022-26"):
        p, f = by_check.get((h, n, True), []), by_check.get((h, n, False), [])
        tot += len(p) + len(f); fail_n += len(f)
        row += f" {sum(p) / len(p) if p else 0:+10.2f} {sum(f) / len(f) if f else 0:+6.2f} {len(f):7d} |"
    row += f" {1 - fail_n / tot:9.0%}"
    L.append(row)


# ---- Part C ----------------------------------------------------------------
class Variant(Opportunity):
    def __init__(self, name=None, how=None):
        super().__init__(OppParams(min_score=6))
        self.name, self.how = name, how

    def checks(self, i):
        ch = super().checks(i)
        if ch is None or self.how != "removed":
            return ch
        return [(n, True if n == self.name else ok) for n, ok in ch]

    def signal(self, i):
        if self.how == "mandatory":
            ch = super().checks(i)
            if ch is None or not dict(ch)[self.name]:
                return None
        return super().signal(i)


VARIANTS = [("live (6 of 8)", None, None)] + [(f"{n} {h}", n, h) for n in NAMES for h in ("removed", "mandatory")]
res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for label, n, h in VARIANTS:
            curve, trades = run(make=lambda n=n, h=h: Variant(n, h), max_open=8, risk=0.005, start=s, end=e)
            res[(o, half, label)] = metrics(curve, trades)

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
REF = VARIANTS[0][0]
ref_dd = med([res[(o, "2022-26", REF)]['dd'] for o in OFFSETS])
L += ["", "Part C - check removed (always passes) or mandatory; 8 slots, 0.5% risk, top 15; medians over six close times",
      f"{'variant':24s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s} {'trades 22-26':>12s} {'wins vs live':>12s} {'(18-21/22-26)':>13s} verdict"]
for label, _, _ in VARIANTS:
    a = [res[(o, "2018-21", label)] for o in OFFSETS]; b = [res[(o, "2022-26", label)] for o in OFFSETS]
    w = sum(res[(o, h, label)]['sharpe'] > res[(o, h, REF)]['sharpe'] for o, h in cells)
    w1 = sum(res[(o, "2018-21", label)]['sharpe'] > res[(o, "2018-21", REF)]['sharpe'] for o in OFFSETS)
    dd = med([m['dd'] for m in b])
    v = "REF" if label == REF else ("PASS" if w >= 10 and dd >= ref_dd - 0.03 else "")
    L.append(f"{label:24s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} "
             f"{med([m['cagr'] for m in b]):+8.1%} / {med([m['sharpe'] for m in b]):4.2f} {dd:9.1%} {med([m['n'] for m in b]):12d} "
             f"{'' if label == REF else f'{w} of 12':>12s} {'' if label == REF else f'{w1}/{w - w1}':>13s} {v}")
print("\n".join(L))

# ---- Part D: the one variant that passed, on round 12's 55-coin pool ------------
# Added after Part C: "trend_up removed" passed the bar on wins mostly from 2018-21
# while its 2022-26 median Sharpe was lower. Bar set before this check: it must
# beat the live rules' Sharpe in BOTH halves on this second data set (more coins,
# 00:00 closes, data from 2017).
ns12 = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r33d'}
exec(src12 := open(_os.path.join(HERE, 'research12.py')).read()[:open(_os.path.join(HERE, 'research12.py')).read().index('\nL = []')], ns12)
L += ["", "Part D - 'trend_up removed' vs live on round 12's 55-coin pool (8 slots, 0.5% risk, top 15)",
      f"{'variant':24s} {'2018-21 ret / Sh / DD':>24s} {'2022-26 ret / Sh / DD':>24s}"]
sh = {}
for label, n, h in (VARIANTS[0], VARIANTS[1]):
    row = f"{label:24s}"
    for half, (s, e) in (("2018-21", (START, SPLIT)), ("2022-26", (SPLIT, None))):
        m = ns12['metrics'](*ns12['run'](make=lambda n=n, h=h: Variant(n, h), max_open=8, risk=0.005, start=s, end=e))
        sh[(label, half)] = m['sharpe']
        row += f" {m['cagr']:+9.1%} / {m['sharpe']:4.2f} / {m['dd']:6.1%}"
    L.append(row)
both = all(sh[(VARIANTS[1][0], h)] > sh[(REF, h)] for h in ("2018-21", "2022-26"))
L.append(f"verdict: {'confirmed on the second data set' if both else 'NOT confirmed on the second data set -> no change'}")
print("\n".join(L[-5:]))
