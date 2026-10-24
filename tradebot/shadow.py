"""Live vs backtest: replay the backtest over the days the live bot has run.

For the evaluation period before any real money: the bot only deserves
trust if its real trades match what the backtest says it should have done
on the same days. This module replays the live rules over the same coins
and dates, with the same capital, slots and risk, and compares the two trade
lists: trades both took, trades only one took, and the entry-price gap.

The replay decides at each daily close and fills at the next open, like the
research backtests (0.1% fee + 0.05% slippage). It uses today's coin list
for every day, while the live bot re-ranks the top 15 daily, so a small
mismatch on coins entering or leaving the list is expected.
"""
import csv
import json
import os
from datetime import datetime, timezone

from tradebot.backtest import FEE, SLIPPAGE
from tradebot.data import fetch_candles
from tradebot.opportunity import Opportunity, OppParams

DAY = 86_400_000


def _day(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d")


def _parse(t):
    return int(datetime.strptime(t.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp() * 1000)


def live_trades(state_dir):
    path = os.path.join(state_dir, "live_trades.csv")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [dict(r, ms=_parse(r["time"])) for r in csv.DictReader(f)]


def replay(candles, start, capital=5000.0, max_open=5, risk=0.01, params=OppParams()):
    """Backtest trades (dicts with day, symbol, side, price) from the candle closing on/after `start`."""
    strats = {s: Opportunity(params).prepare(cs) for s, cs in candles.items()}
    idx = {s: {c.open_time: i for i, c in enumerate(cs)} for s, cs in candles.items()}
    times = sorted(t for t in set(t for s in idx for t in idx[s]) if t + DAY > start)
    cash, pos, pending, out = capital, {}, {}, []
    for t in times:
        eq = cash + sum(q["qty"] * candles[s][idx[s][t]].open for s, q in pos.items() if t in idx[s])
        for s, (side, plan) in sorted(pending.items(), key=lambda x: x[1][0] != "SELL"):
            i = idx[s].get(t)
            if i is None:
                continue
            o = candles[s][i].open
            if side == "SELL" and s in pos:
                q = pos.pop(s); cash += q["qty"] * o * (1 - SLIPPAGE) * (1 - FEE)
                out.append({"day": _day(t), "symbol": s, "side": "SELL", "price": o * (1 - SLIPPAGE)})
        for s, (side, plan) in sorted(pending.items(), key=lambda x: -(x[1][1].score if x[1][1] else 0)):
            i = idx[s].get(t)
            if side != "BUY" or i is None or s in pos or len(pos) >= max_open:
                continue
            entry = candles[s][i].open * (1 + SLIPPAGE)
            if entry <= plan.stop:
                continue
            qty = min(eq * risk / (entry - plan.stop), cash * (1 - FEE) / entry)
            if qty > 0:
                cash -= qty * entry / (1 - FEE)
                pos[s] = {"qty": qty, "stop": plan.stop, "peak": entry}
                out.append({"day": _day(t), "symbol": s, "side": "BUY", "price": entry})
        pending = {}
        for s, cs in candles.items():
            i = idx[s].get(t)
            if i is None or t + DAY <= start:
                continue
            c, st = cs[i], strats[s]
            if s in pos:
                q = pos[s]
                if c.low <= q["stop"]:
                    pending[s] = ("SELL", None); continue
                st.peak = max(q["peak"], c.close); q["peak"] = st.peak
                q["stop"] = st.update_stop(i, q["stop"])
            else:
                plan = st.signal(i)
                if plan:
                    pending[s] = ("BUY", plan)
    return out


def compare(live, shadow, tolerance_days=1):
    """Match live and backtest trades by coin, side and date (within a day)."""
    used, both, only_live = set(), [], []
    for lt in live:
        lday = datetime.strptime(lt["time"][:10], "%Y-%m-%d")
        hit = None
        for k, st in enumerate(shadow):
            if k in used or st["symbol"] != lt["symbol"] or st["side"] != lt["side"]:
                continue
            if abs((datetime.strptime(st["day"], "%Y-%m-%d") - lday).days) <= tolerance_days:
                hit = k; break
        if hit is None:
            only_live.append(lt)
        else:
            used.add(hit); both.append((lt, shadow[hit]))
    only_shadow = [st for k, st in enumerate(shadow) if k not in used]
    return both, only_live, only_shadow


def unlisted(state_dir):
    """Coins the live log says the exchange doesn't list (the bot skips them)."""
    path = os.path.join(state_dir, "run.log")
    if not os.path.exists(path):
        return set()
    with open(path) as f:
        return {line.split("] ", 1)[1].split(":", 1)[0] for line in f
                if "skipped, not tradable on this exchange" in line and "] " in line}


def shadow_report(state_dir, symbols, capital=5000.0, max_open=5, risk=0.01, fetch=fetch_candles, min_score=5, ignore=()):
    live = [t for t in live_trades(state_dir) if t["reason"] not in ("manual", "backstop")]
    symbols = [s for s in symbols if s not in unlisted(state_dir)]
    lines = ["live vs backtest (same coins, dates, capital and rules):"]
    if not live:
        return lines + ["  no live trades yet"]
    start = min(t["ms"] for t in live) - DAY   # the candle whose close produced the first trade
    p = OppParams(min_score=min_score, ignore=ignore)
    syms = sorted(set(symbols) | {t["symbol"] for t in live})
    days_needed = int((max(t["ms"] for t in live) - start) / DAY) + p.warmup + 70
    candles = {}
    for s in syms:
        try:
            candles[s] = fetch(s, "1d", days_needed)
        except OSError:
            pass
    shadow = replay(candles, start, capital, max_open, risk, p)
    both, only_live, only_shadow = compare(live, shadow)
    gaps = [(lt_price / st["price"] - 1) * (1 if lt["side"] == "BUY" else -1)
            for lt, st in both for lt_price in [float(lt["price"])]]
    lines.append(f"  since {_day(start + DAY)}: {len(both)} trades matched, {len(only_live)} only live, "
                 f"{len(only_shadow)} only in the backtest")
    if gaps:
        lines.append(f"  matched trades: live price {sum(gaps) / len(gaps) * 100:+.2f}% vs backtest on average "
                     f"(positive = live filled worse)")
    for lt in only_live:
        lines.append(f"  only live:     {lt['time'][:10]} {lt['side']:4} {lt['symbol']}")
    for st in only_shadow:
        lines.append(f"  only backtest: {st['day']} {st['side']:4} {st['symbol']}")
    if not only_live and not only_shadow:
        lines.append("  the live bot did exactly what the backtest would have done")
    return lines
