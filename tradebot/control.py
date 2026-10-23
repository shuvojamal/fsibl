"""Owner controls written by the dashboard app, read by the daily workflow.

The app can't edit code, so it writes small files into the state directory
through GitHub's contents API:

    settings.json   capital, risk per trade, max positions, backstop, limits, gold,
                    days before a coin sold by hand may be bought again, checks
                    required to buy (min_score, 4-7; research round 24)
                    (alert_pct is read only by the app)
    CLOSE           symbols to sell at market on the next run, or ALL
    RESET_HALT      clear a tripped circuit breaker
    PAUSED          no new entries (exits keep running)

For the owner's real-money account (binance_live/ on the VPS), settings.json
also carries "mode": "off" | "test" | "live". "test" connects with the real
keys and decides, but places no orders (--dry-run). "live" trades real money
and is only accepted together with "confirm": "I ACCEPT THE RISK", typed by
the owner in the app; anything else falls back to "off".

Everything is validated and clamped here before it reaches a command line,
so a typo in the app can't produce a dangerous or broken run.
"""
import json
import os
import re

CONFIRM = "I ACCEPT THE RISK"

# name: (default, lowest allowed, highest allowed)
LIMITS = {
    "capital": (5000.0, 100.0, 1_000_000.0),
    "risk_pct": (1.0, 0.25, 2.0),
    "max_open": (5, 1, 10),
    "backstop_pct": (20.0, 0.0, 50.0),
    "max_drawdown_pct": (35.0, 10.0, 60.0),
    "daily_loss_pct": (3.0, 1.0, 10.0),
    "rebuy_wait_days": (7, 0, 30),
    "min_score": (5, 4, 7),
}


def read_controls(state_dir, default_capital=5000.0):
    notes = []
    raw = {}
    path = os.path.join(state_dir, "settings.json")
    if os.path.exists(path):
        try:
            with open(path) as f:
                raw = json.load(f)
            if not isinstance(raw, dict):
                raise ValueError("not an object")
        except ValueError as e:
            notes.append(f"settings.json ignored ({e}); using defaults")
            raw = {}
    out = {}
    for key, (default, lo, hi) in LIMITS.items():
        if key == "capital":
            default = default_capital
        v = raw.get(key, default)
        try:
            v = float(v)
        except (TypeError, ValueError):
            notes.append(f"{key}={v!r} is not a number; using {default}")
            v = float(default)
        if not lo <= v <= hi:
            notes.append(f"{key}={v:g} outside {lo:g}..{hi:g}; clamped")
            v = min(hi, max(lo, v))
        out[key] = int(v) if isinstance(default, int) else v
    out["gold"] = bool(raw.get("gold", True))
    mode = raw.get("mode", "off")
    if mode not in ("off", "test", "live"):
        notes.append(f"mode={mode!r} unknown; using off")
        mode = "off"
    if mode == "live" and raw.get("confirm") != CONFIRM:
        notes.append("mode=live without the typed confirmation; using off")
        mode = "off"
    out["mode"] = mode

    close = []
    cpath = os.path.join(state_dir, "CLOSE")
    if os.path.exists(cpath):
        with open(cpath) as f:
            for tok in f.read().upper().split():
                if tok == "ALL" or re.fullmatch(r"[A-Z0-9]{2,15}USDT", tok):
                    close.append(tok)
                else:
                    notes.append(f"CLOSE: ignored {tok[:20]!r}")
    out["close"] = sorted(set(close))
    out["reset_halt"] = os.path.exists(os.path.join(state_dir, "RESET_HALT"))
    out["paused"] = os.path.exists(os.path.join(state_dir, "PAUSED"))
    out["notes"] = notes
    return out


def live_args(c):
    """The `tradebot live` flags these controls translate to (all values validated above)."""
    cap = c["capital"]
    args = ["--risk", f"{c['risk_pct'] / 100:.4f}", "--capital", f"{cap:.2f}",
            "--trade-usdt", f"{cap:.2f}", "--max-trade-usdt", f"{cap:.2f}",
            "--max-daily-loss", f"{cap * c['daily_loss_pct'] / 100:.2f}",
            "--max-drawdown", f"{c['max_drawdown_pct'] / 100:.4f}",
            "--max-open", str(c["max_open"]), "--backstop", f"{c['backstop_pct'] / 100:.4f}",
            "--rebuy-wait-days", str(c["rebuy_wait_days"]), "--min-score", str(c["min_score"])]
    if c["paused"]:
        args.append("--pause-entries")
    if c["reset_halt"]:
        args.append("--reset-halt")
    if c["close"]:
        args += ["--close-now"] + c["close"]
    return args


def real_money_flags(c):
    """Extra `tradebot live` flags for the real-money account, or None while it is off."""
    if c["mode"] == "live":
        return ["--live", "--i-accept-the-risk"]
    if c["mode"] == "test":
        return ["--live", "--i-accept-the-risk", "--dry-run"]   # real keys, no orders
    return None
