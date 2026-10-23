"""Fetch candlestick (kline) data from Binance's public market-data API.

No API key is needed. data-api.binance.vision serves market data only and
is reachable from regions where api.binance.com is blocked.
"""
import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass

BASE_URL = "https://data-api.binance.vision/api/v3/klines"
MAX_LIMIT = 1000

INTERVAL_MS = {
    "1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1h": 3_600_000, "2h": 7_200_000, "4h": 14_400_000, "6h": 21_600_000,
    "8h": 28_800_000, "12h": 43_200_000, "1d": 86_400_000,
}


@dataclass
class Candle:
    open_time: int  # ms since epoch
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int


def _get(params):
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                return json.load(resp)
        except OSError:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def ticker_price(symbol):
    """Binance's current price for a symbol (the same public data the signals use)."""
    url = BASE_URL.replace("/klines", "/ticker/price") + "?" + urllib.parse.urlencode({"symbol": symbol.upper()})
    with urllib.request.urlopen(url, timeout=15) as resp:
        return float(json.load(resp)["price"])


def fetch_candles(symbol, interval, count):
    """Return the most recent `count` *closed* candles, oldest first."""
    if interval not in INTERVAL_MS:
        raise ValueError(f"unsupported interval {interval!r}")
    now_ms = int(time.time() * 1000)
    candles = []
    end_time = None
    # Page backwards until we have enough history.
    while len(candles) < count + 1:
        params = {"symbol": symbol.upper(), "interval": interval,
                  "limit": min(MAX_LIMIT, count + 1 - len(candles))}
        if end_time is not None:
            params["endTime"] = end_time
        rows = _get(params)
        if not rows:
            break
        batch = [Candle(int(r[0]), float(r[1]), float(r[2]), float(r[3]),
                        float(r[4]), float(r[5]), int(r[6])) for r in rows]
        candles = batch + candles
        end_time = batch[0].open_time - 1
        if len(rows) < params["limit"]:
            break
    # Drop the candle that is still forming.
    candles = [c for c in candles if c.close_time < now_ms]
    return candles[-count:]
