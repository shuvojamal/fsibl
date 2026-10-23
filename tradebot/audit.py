"""State audit: check a live/demo state directory for internal consistency.

Run after every scheduled bot run (idea from PkLavc/Autotrader's
scripts/audit_state.py). A failed check means the bot's books disagree with
themselves, e.g. a partial sell left coins behind that the bot no longer
tracks, or a stop that can never trigger. It does not touch the exchange.
"""
import csv
import json
import math
import os


def _read(path, rows=False):
    with open(path, newline="") as f:
        return list(csv.DictReader(f)) if rows else json.load(f)


def audit(state_dir, max_open=0):
    """Return a list of problems found (empty list = all checks passed)."""
    problems = []
    state_path = os.path.join(state_dir, "live_state.json")
    if not os.path.exists(state_path):
        return [f"{state_path} is missing"]
    try:
        state = _read(state_path)
    except ValueError as e:
        return [f"{state_path} is not valid JSON: {e}"]
    positions = state.get("positions", {})
    held = {s: p for s, p in positions.items() if p.get("qty", 0) > 0}

    for s, p in held.items():
        for k in ("qty", "entry", "stop"):
            v = p.get(k)
            if not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
                problems.append(f"{s}: {k} is {v!r}, expected a positive number")
        stop, top = p.get("stop", 0), max(p.get("peak", 0) or 0, p.get("entry", 0) or 0)
        if top and stop >= top:
            problems.append(f"{s}: stop {stop:g} is at or above the highest price held ({top:g}); it would sell at once")
    if max_open and len(held) > max_open:
        problems.append(f"{len(held)} positions open, more than the cap of {max_open}")

    trades = []
    tpath = os.path.join(state_dir, "live_trades.csv")
    if os.path.exists(tpath):
        trades = _read(tpath, rows=True)
    net, realised = {}, 0.0
    for r in trades:
        q = float(r["qty"])
        net[r["symbol"]] = net.get(r["symbol"], 0.0) + (q if r["side"] == "BUY" else -q)
        if r["side"] == "SELL" and r.get("pnl_usdt"):
            realised += float(r["pnl_usdt"])
    for s in set(net) | set(held):
        logged, tracked = net.get(s, 0.0), held.get(s, {}).get("qty", 0.0)
        if abs(logged - tracked) > 1e-6 * max(abs(logged), abs(tracked), 1e-12) + 1e-12:
            problems.append(f"{s}: trade log nets to {logged:g} but the state holds {tracked:g}")
    if abs(realised - state.get("realised", 0.0)) > 0.01 + 1e-4 * len(trades):
        problems.append(f"realised P&L in state {state.get('realised', 0.0):.4f} != sum of SELL rows {realised:.4f}")

    epath = os.path.join(state_dir, "equity.csv")
    if os.path.exists(epath):
        rows = _read(epath, rows=True)
        times = [r["time"] for r in rows]
        if times != sorted(times):
            problems.append("equity.csv times are out of order")
        for r in rows:
            if not math.isfinite(float(r["equity"])) or float(r["equity"]) <= 0:
                problems.append(f"equity.csv has a bad equity value at {r['time']}: {r['equity']}")
        if rows and int(rows[-1]["open_positions"]) != len(held):
            problems.append(f"equity.csv last row says {rows[-1]['open_positions']} open, state holds {len(held)}")
    return problems
