"""Minimal signed client for the Binance Spot REST API.

Works against the Spot Testnet (default) or the live exchange. Keys are read
from environment variables so they never sit in a file in this repo:

    BINANCE_API_KEY, BINANCE_API_SECRET

Only the handful of endpoints the bot needs are wrapped. `transport` can be
replaced in tests with a function that fakes the exchange.
"""
import hashlib
import hmac
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request

TESTNET_URL = "https://testnet.binance.vision"
LIVE_URL = "https://api.binance.com"


class BinanceError(Exception):
    def __init__(self, status, code, msg):
        super().__init__(f"HTTP {status} code {code}: {msg}")
        self.status, self.code, self.msg = status, code, msg


def http_transport(method, url, headers, body):
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


class BinanceClient:
    def __init__(self, api_key=None, api_secret=None, base_url=TESTNET_URL,
                 transport=http_transport, recv_window=5000):
        self.api_key = api_key or os.environ.get("BINANCE_API_KEY", "")
        self.api_secret = (api_secret or os.environ.get("BINANCE_API_SECRET", "")).encode()
        self.base_url = base_url.rstrip("/")
        self.transport = transport
        self.recv_window = recv_window
        self._filters = {}
        self._time_offset = 0

    # -- plumbing ---------------------------------------------------------

    def _request(self, method, path, params=None, signed=False):
        params = {k: v for k, v in (params or {}).items() if v is not None}
        headers = {"X-MBX-APIKEY": self.api_key} if self.api_key else {}
        if signed:
            if not self.api_key or not self.api_secret:
                raise BinanceError(0, -1, "BINANCE_API_KEY / BINANCE_API_SECRET not set")
            params["timestamp"] = int(time.time() * 1000) + self._time_offset
            params["recvWindow"] = self.recv_window
            query = urllib.parse.urlencode(params)
            params["signature"] = hmac.new(self.api_secret, query.encode(), hashlib.sha256).hexdigest()
        query = urllib.parse.urlencode(params)
        url = f"{self.base_url}{path}"
        body = None
        if method in ("POST", "PUT", "DELETE") and query:
            body = query.encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif query:
            url += "?" + query
        status, raw = self.transport(method, url, headers, body)
        data = json.loads(raw) if raw else {}
        if status >= 400 or (isinstance(data, dict) and data.get("code", 0) < 0):
            raise BinanceError(status, data.get("code") if isinstance(data, dict) else None,
                               data.get("msg") if isinstance(data, dict) else raw[:200])
        return data

    def sync_time(self):
        server = self._request("GET", "/api/v3/time")["serverTime"]
        self._time_offset = server - int(time.time() * 1000)
        return self._time_offset

    # -- market data ------------------------------------------------------

    def price(self, symbol):
        return float(self._request("GET", "/api/v3/ticker/price", {"symbol": symbol})["price"])

    def symbol_filters(self, symbol):
        """Lot-size step, minimum notional and price tick for a symbol."""
        if symbol not in self._filters:
            info = self._request("GET", "/api/v3/exchangeInfo", {"symbol": symbol})
            f = {x["filterType"]: x for x in info["symbols"][0]["filters"]}
            self._filters[symbol] = {
                "step": float(f["LOT_SIZE"]["stepSize"]),
                "min_qty": float(f["LOT_SIZE"]["minQty"]),
                "tick": float(f["PRICE_FILTER"]["tickSize"]),
                "min_notional": float(f.get("NOTIONAL", f.get("MIN_NOTIONAL", {})).get("minNotional", 0)),
            }
        return self._filters[symbol]

    def round_qty(self, symbol, qty):
        """Round a quantity *down* to the symbol's lot step, as a string Binance accepts."""
        step = self.symbol_filters(symbol)["step"]
        decimals = max(0, -int(round(math.log10(step)))) if step < 1 else 0
        qty = math.floor(qty / step) * step
        return f"{qty:.{decimals}f}"

    # -- account ----------------------------------------------------------

    def balances(self):
        acct = self._request("GET", "/api/v3/account", signed=True)
        return {b["asset"]: float(b["free"]) for b in acct["balances"] if float(b["free"]) > 0}

    def open_orders(self, symbol=None):
        return self._request("GET", "/api/v3/openOrders", {"symbol": symbol}, signed=True)

    # -- orders -----------------------------------------------------------

    def market_order(self, symbol, side, qty=None, quote_qty=None):
        """Market buy/sell. Give `qty` in the coin, or `quote_qty` in USDT for buys."""
        params = {"symbol": symbol, "side": side.upper(), "type": "MARKET",
                  "newOrderRespType": "FULL"}
        if quote_qty is not None:
            params["quoteOrderQty"] = f"{quote_qty:.2f}"
        else:
            params["quantity"] = self.round_qty(symbol, qty)
        return self._request("POST", "/api/v3/order", params, signed=True)

    def test_order(self, symbol, side, qty=None, quote_qty=None):
        """Validate an order without placing it (checks keys, filters, balance)."""
        params = {"symbol": symbol, "side": side.upper(), "type": "MARKET"}
        if quote_qty is not None:
            params["quoteOrderQty"] = f"{quote_qty:.2f}"
        else:
            params["quantity"] = self.round_qty(symbol, qty)
        return self._request("POST", "/api/v3/order/test", params, signed=True)

    def cancel_all(self, symbol):
        try:
            return self._request("DELETE", "/api/v3/openOrders", {"symbol": symbol}, signed=True)
        except BinanceError as e:
            if e.code == -2011:  # nothing to cancel
                return []
            raise


def fill_summary(order):
    """(executed qty, average price, commission in quote) from a FULL order response."""
    qty = float(order.get("executedQty", 0))
    quote = float(order.get("cummulativeQuoteQty", 0))
    avg = quote / qty if qty else 0.0
    commission = 0.0
    for f in order.get("fills", []):
        c, asset = float(f["commission"]), f["commissionAsset"]
        # Commission is charged in the quote (USDT), the base coin, or BNB.
        # BNB-paid fees are left out: they come from a separate balance.
        if order["symbol"].endswith(asset):
            commission += c
        elif order["symbol"].startswith(asset):
            commission += c * float(f["price"])
    return qty, avg, commission
