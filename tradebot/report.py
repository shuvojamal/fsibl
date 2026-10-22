"""One-screen status report for a live/demo run: balances, open positions with
unrealised P&L, realised trades, and today's score for every symbol."""
import csv
import json
import os

from tradebot.data import fetch_candles
from tradebot.opportunity import Opportunity, OppParams


def load_state(state_dir):
    path = os.path.join(state_dir, "live_state.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def realised(state_dir):
    """(number of closed trades, total realised P&L in USDT, list of rows)."""
    path = os.path.join(state_dir, "live_trades.csv")
    if not os.path.exists(path):
        return 0, 0.0, []
    with open(path) as f:
        rows = list(csv.DictReader(f))
    sells = [r for r in rows if r["side"] == "SELL" and r.get("pnl_usdt")]
    return len(sells), sum(float(r["pnl_usdt"]) for r in sells), rows


def report(client, state_dir, symbols, interval="1d", params=None, lines=None):
    """Build the report as a list of lines. `client` may be None (no account section)."""
    out = lines if lines is not None else []
    state = load_state(state_dir)
    positions = state.get("positions", {})
    p = params or OppParams()

    if client is not None:
        bal = client.balances()
        usdt = bal.get("USDT", 0.0)
        out.append(f"venue: {getattr(client, 'label', client.base_url)}")
        out.append(f"free USDT: {usdt:,.2f}")

    open_pos = {s: q for s, q in positions.items() if q.get("qty", 0) > 0}
    total_unreal = 0.0
    out.append(f"\nopen positions: {len(open_pos)}")
    if open_pos:
        out.append(f"  {'symbol':9} {'qty':>14} {'entry':>12} {'now':>12} {'stop':>12} {'P&L':>9} {'P&L %':>7} {'to stop':>8}")
        for s, q in open_pos.items():
            price = client.price(s) if client is not None else fetch_candles(s, interval, 2)[-1].close
            pnl = (price - q["entry"]) * q["qty"]
            total_unreal += pnl
            out.append(f"  {s:9} {q['qty']:>14.6f} {q['entry']:>12.6g} {price:>12.6g} {q['stop']:>12.6g} "
                       f"{pnl:>+9.2f} {price / q['entry'] - 1:>+7.2%} {q['stop'] / price - 1:>+8.2%}")
        out.append(f"  unrealised total: {total_unreal:+.2f} USDT")

    n, pnl, rows = realised(state_dir)
    out.append(f"\nclosed trades: {n}, realised P&L: {pnl:+.2f} USDT")
    for r in rows[-10:]:
        out.append(f"  {r['time']} {r['side']:4} {r['symbol']:9} {float(r['qty']):.6f} @ {float(r['price']):.6g} "
                   f"{r['reason']} {r.get('pnl_usdt', '')}")

    out.append(f"\ntoday's score ({interval} candles, need {p.min_score} of {Opportunity.CHECKS}):")
    for s in symbols:
        try:
            cs = fetch_candles(s, interval, p.warmup + 60)
        except OSError as e:
            out.append(f"  {s:9} data error: {e}")
            continue
        o = Opportunity(p).prepare(cs)
        ch = o.checks(len(cs) - 1)
        if ch is None:
            out.append(f"  {s:9} warming up")
            continue
        score = sum(ok for _, ok in ch)
        flag = "IN " if s in open_pos else ("** " if score >= p.min_score else "   ")
        out.append(f"  {flag}{s:9} {score}/8  {', '.join(n for n, ok in ch if ok)}")
    return out
