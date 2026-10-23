"""Funding-rate carry monitor (research round 13).

Buying a coin on spot and shorting the same amount on the perpetual swap is
price-neutral and collects the funding rate while it is positive. Round 13
found this pays well only when funding spikes (2020-21: about +16% to +88% a
year on capital) and earns less than a stablecoin deposit in quiet markets
(2024-26: about +3% a year). So this module only watches: it reads OKX's
public funding history (no keys) and flags coins whose trailing 7-day funding
is high enough to be worth the two-leg trade.
"""
import json
import urllib.request

OKX_URL = "https://www.okx.com"
WEEK_MS = 7 * 86_400_000
# Annualised 7-day funding at which carry beats a ~5% stablecoin yield with
# room to spare: at 1x margin half the capital sits in the short's margin,
# so 20% funding is about 10% a year on the whole capital, before costs.
FLAG_AT = 0.20


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "tradebot/0.1"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def trailing_funding(coin, get=_get):
    """Annualised average funding over the last 7 days, or None if unavailable."""
    data = get(f"{OKX_URL}/api/v5/public/funding-rate-history?instId={coin}-USDT-SWAP&limit=100").get("data") or []
    if not data:
        return None
    newest = max(int(r["fundingTime"]) for r in data)
    week = [float(r["realizedRate"] or r["fundingRate"]) for r in data if int(r["fundingTime"]) > newest - WEEK_MS]
    return sum(week) / 7 * 365


def scan_funding(coins, get=_get):
    rows = []
    for c in coins:
        c = c.upper().replace("USDT", "")
        try:
            rows.append((c, trailing_funding(c, get)))
        except Exception:
            rows.append((c, None))
    return sorted(rows, key=lambda r: -(r[1] if r[1] is not None else -9))


def format_funding(rows, flag_at=FLAG_AT):
    out = [f"funding carry (OKX perps, trailing 7 days, annualised; flag at {flag_at:.0%}):"]
    for c, f in rows:
        if f is None:
            out.append(f"     {c:6s}  no perpetual / no data")
        else:
            out.append(f"  {'**' if f >= flag_at else '  '} {c:6s}  {f:+7.1%}/yr" + ("  CARRY OPPORTUNITY" if f >= flag_at else ""))
    if not any(f is not None and f >= flag_at for _, f in rows):
        out.append("no carry opportunity today: funding is too low to beat holding stablecoins")
    return out
