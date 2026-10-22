"""Opportunity scan: rank a pool of coins by trailing 90-day dollar volume,
keep the top N (the research-round-9 universe rule), and score each one."""
from tradebot.data import fetch_candles
from tradebot.opportunity import Opportunity, OppParams

POOL = ("BTC ETH SOL XRP DOGE ADA LINK AVAX DOT LTC BNB TRX ATOM UNI NEAR FIL ETC XLM ALGO AAVE "
        "BCH SUI PEPE ARB OP APT INJ FET TIA SEI ZEC CRV RUNE IMX STX SHIB HBAR ICP GRT VET").split()


def scan(pool=POOL, top=15, interval="1d", params=None):
    """Return (rows, skipped). Each row: (symbol, 90d dollar volume, score, missing checks, plan or None, close)."""
    p = params or OppParams()
    rows, skipped = [], []
    for base in pool:
        sym = base.upper() + ("" if base.upper().endswith("USDT") else "USDT")
        try:
            cs = fetch_candles(sym, interval, p.warmup + 60)
        except Exception:
            skipped.append(sym)
            continue
        dv = sum(c.volume * c.close for c in cs[-90:])
        o = Opportunity(p).prepare(cs)
        i = len(cs) - 1
        ch = o.checks(i)
        if ch is None:
            skipped.append(sym)
            continue
        rows.append((sym, dv, sum(ok for _, ok in ch), [n for n, ok in ch if not ok], o.signal(i), cs[i].close))
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows[:top], skipped


def format_scan(rows, min_score=5):
    out = [f"{'':7}{'symbol':10} {'90d volume':>12} {'score':>5} {'close':>12} {'stop':>12} {'risk':>6}  missing"]
    for sym, dv, sc, missing, plan, close in rows:
        tag = "SIGNAL" if plan else ""
        stop = f"{plan.stop:12.6g}" if plan else " " * 12  # 6 significant digits: PEPE trades at 0.000005
        risk = f"{(close - plan.stop) / close:6.1%}" if plan else " " * 6
        out.append(f"{tag:7}{sym:10} {dv / 1e9:>10.1f}bn {sc:>3}/8 {close:>12.6g} {stop} {risk}  {', '.join(missing)}")
    return out
