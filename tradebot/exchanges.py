"""Public best-bid/ask fetchers for nine spot exchanges. No keys needed.

Fees are standard (lowest-tier) spot *taker* fees, since arbitrage has to
take whatever price is there right now. Check them against your own
account: VIP tiers, BNB discounts, and promotions change the numbers.
"""
import json
import urllib.request
from dataclasses import dataclass


@dataclass
class Quote:
    exchange: str
    symbol: str       # canonical, e.g. BTCUSDT
    bid: float
    bid_qty: float
    ask: float
    ask_qty: float


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "tradebot/0.1"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.load(resp)


def _split(sym):
    """BTCUSDT -> ('BTC', 'USDT')."""
    for quote in ("USDT", "USDC", "BTC"):
        if sym.endswith(quote) and len(sym) > len(quote):
            return sym[:-len(quote)], quote
    raise ValueError(sym)


def binance(sym):
    d = _get(f"https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol={sym}")
    return Quote("binance", sym, float(d["bidPrice"]), float(d["bidQty"]),
                 float(d["askPrice"]), float(d["askQty"]))


def kraken(sym):
    base, quote = _split(sym)
    pair = ("XBT" if base == "BTC" else base) + quote
    d = _get(f"https://api.kraken.com/0/public/Ticker?pair={pair}")
    if d["error"]:
        raise OSError(d["error"])
    t = next(iter(d["result"].values()))
    return Quote("kraken", sym, float(t["b"][0]), float(t["b"][2]), float(t["a"][0]), float(t["a"][2]))


def coinbase(sym):
    base, quote = _split(sym)
    d = _get("https://api.coinbase.com/api/v3/brokerage/market/product_book"
             f"?product_id={base}-{quote}&limit=1")["pricebook"]
    b, a = d["bids"][0], d["asks"][0]
    return Quote("coinbase", sym, float(b["price"]), float(b["size"]), float(a["price"]), float(a["size"]))


def okx(sym):
    base, quote = _split(sym)
    t = _get(f"https://www.okx.com/api/v5/market/ticker?instId={base}-{quote}")["data"][0]
    return Quote("okx", sym, float(t["bidPx"]), float(t["bidSz"]), float(t["askPx"]), float(t["askSz"]))


def kucoin(sym):
    base, quote = _split(sym)
    t = _get(f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={base}-{quote}")["data"]
    return Quote("kucoin", sym, float(t["bestBid"]), float(t["bestBidSize"]),
                 float(t["bestAsk"]), float(t["bestAskSize"]))


def gate(sym):
    base, quote = _split(sym)
    t = _get(f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={base}_{quote}")[0]
    return Quote("gate", sym, float(t["highest_bid"]), float(t["highest_size"]),
                 float(t["lowest_ask"]), float(t["lowest_size"]))


def bitget(sym):
    t = _get(f"https://api.bitget.com/api/v2/spot/market/tickers?symbol={sym}")["data"][0]
    return Quote("bitget", sym, float(t["bidPr"]), float(t["bidSz"]), float(t["askPr"]), float(t["askSz"]))


def mexc(sym):
    d = _get(f"https://api.mexc.com/api/v3/ticker/bookTicker?symbol={sym}")
    return Quote("mexc", sym, float(d["bidPrice"]), float(d["bidQty"]),
                 float(d["askPrice"]), float(d["askQty"]))


def htx(sym):
    t = _get(f"https://api.htx.com/market/detail/merged?symbol={sym.lower()}")["tick"]
    return Quote("htx", sym, t["bid"][0], t["bid"][1], t["ask"][0], t["ask"][1])


# name -> (fetcher, taker fee as a fraction)
EXCHANGES = {
    "binance": (binance, 0.0010),
    "kraken": (kraken, 0.0040),
    "coinbase": (coinbase, 0.0120),
    "okx": (okx, 0.0010),
    "kucoin": (kucoin, 0.0010),
    "gate": (gate, 0.0020),
    "bitget": (bitget, 0.0010),
    "mexc": (mexc, 0.0005),
    "htx": (htx, 0.0020),
}
