"""Signed client for the OKX V5 REST API, demo trading by default.

Keys come from environment variables:
    OKX_API_KEY, OKX_API_SECRET, OKX_PASSPHRASE

Demo and live use the same host; the `x-simulated-trading: 1` header routes
requests to the simulated account. Order responses are reshaped to look like
Binance's so the live trader and `fill_summary` work unchanged.
"""
import base64
import hashlib
import hmac
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from tradebot.binance_client import BinanceError

OKX_URL = "https://www.okx.com"


def http_transport(method, url, headers, body):
    # OKX answers 403 to Python's default User-Agent.
    headers = {"User-Agent": "tradebot/0.1", **headers}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def inst_id(symbol):
    """BTCUSDT -> BTC-USDT."""
    for quote in ("USDT", "USDC", "BTC"):
        if symbol.endswith(quote) and len(symbol) > len(quote):
            return f"{symbol[:-len(quote)]}-{quote}"
    raise ValueError(symbol)


class OKXClient:
    label = "OKX DEMO"

    def __init__(self, api_key=None, api_secret=None, passphrase=None, demo=True,
                 transport=http_transport):
        self.api_key = api_key or os.environ.get("OKX_API_KEY", "")
        self.api_secret = (api_secret or os.environ.get("OKX_API_SECRET", "")).encode()
        self.passphrase = passphrase or os.environ.get("OKX_PASSPHRASE", "")
        self.demo = demo
        self.base_url = OKX_URL
        self.transport = transport
        self._filters = {}
        self._time_offset = 0.0
        if not demo:
            self.label = "OKX LIVE"

    # -- plumbing ---------------------------------------------------------

    def _request(self, method, path, params=None, body=None, signed=False):
        params = {k: v for k, v in (params or {}).items() if v is not None}
        query = ("?" + urllib.parse.urlencode(params)) if params else ""
        request_path = path + query
        payload = json.dumps(body) if body is not None else ""
        headers = {"Content-Type": "application/json"}
        if self.demo:
            headers["x-simulated-trading"] = "1"
        if signed:
            if not (self.api_key and self.api_secret and self.passphrase):
                raise BinanceError(0, -1, "OKX_API_KEY / OKX_API_SECRET / OKX_PASSPHRASE not set")
            ts = datetime.fromtimestamp(time.time() + self._time_offset, timezone.utc)
            ts = ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond // 1000:03d}Z"
            msg = ts + method + request_path + payload
            sign = base64.b64encode(hmac.new(self.api_secret, msg.encode(), hashlib.sha256).digest())
            headers.update({"OK-ACCESS-KEY": self.api_key, "OK-ACCESS-SIGN": sign.decode(),
                            "OK-ACCESS-TIMESTAMP": ts, "OK-ACCESS-PASSPHRASE": self.passphrase})
        status, raw = self.transport(method, self.base_url + request_path, headers,
                                     payload.encode() if payload else None)
        try:
            data = json.loads(raw) if raw else {}
        except ValueError:
            raise BinanceError(status, None, f"non-JSON reply from OKX: {raw[:120]!r}")
        code = str(data.get("code", "0")) if isinstance(data, dict) else "?"
        if status >= 400 or code != "0":
            msg = data.get("msg", "") if isinstance(data, dict) else raw[:200]
            # order endpoints put the real reason one level down
            if isinstance(data, dict) and data.get("data"):
                first = data["data"][0]
                msg = f"{msg} {first.get('sCode', '')} {first.get('sMsg', '')}".strip()
            raise BinanceError(status, code, msg)
        return data["data"]

    def sync_time(self):
        server = int(self._request("GET", "/api/v5/public/time")[0]["ts"]) / 1000
        self._time_offset = server - time.time()
        return int(self._time_offset * 1000)

    # -- market data ------------------------------------------------------

    def price(self, symbol):
        return float(self._request("GET", "/api/v5/market/ticker", {"instId": inst_id(symbol)})[0]["last"])

    def symbol_filters(self, symbol):
        if symbol not in self._filters:
            d = self._request("GET", "/api/v5/public/instruments",
                              {"instType": "SPOT", "instId": inst_id(symbol)})[0]
            self._filters[symbol] = {
                "step": float(d["lotSz"]),
                "min_qty": float(d["minSz"]),
                "tick": float(d["tickSz"]),
                # OKX has no notional floor on spot; minSz is in base coin. Keep a
                # small USDT floor so risk-sized orders don't come out microscopic.
                "min_notional": 1.0,
            }
        return self._filters[symbol]

    def round_qty(self, symbol, qty):
        step = self.symbol_filters(symbol)["step"]
        decimals = max(0, -int(round(math.log10(step)))) if step < 1 else 0
        qty = math.floor(qty / step) * step
        return f"{qty:.{decimals}f}"

    # -- account ----------------------------------------------------------

    def balances(self):
        """Free USDT/USDC, and the full amount of every other coin.

        Coins count frozen amounts too (cashBal): a resting backstop order
        freezes the coin it would sell, and the position is still ours.
        """
        details = self._request("GET", "/api/v5/account/balance", signed=True)[0]["details"]
        out = {}
        for d in details:
            key = "availBal" if d["ccy"] in ("USDT", "USDC") else "cashBal"
            v = float(d.get(key) or d.get("availBal") or 0)
            if v > 0:
                out[d["ccy"]] = v
        return out

    # -- orders -----------------------------------------------------------

    def market_order(self, symbol, side, qty=None, quote_qty=None):
        """Market buy/sell, returned in Binance's FULL-order shape."""
        body = {"instId": inst_id(symbol), "tdMode": "cash", "side": side.lower(),
                "ordType": "market"}
        if quote_qty is not None:
            body["sz"], body["tgtCcy"] = f"{quote_qty:.2f}", "quote_ccy"
        else:
            body["sz"], body["tgtCcy"] = self.round_qty(symbol, qty), "base_ccy"
        placed = self._request("POST", "/api/v5/trade/order", body=body, signed=True)[0]
        order_id = placed["ordId"]
        # Market orders fill at once, but the placement response carries no fill
        # details; fetch the order to get size, average price and fee.
        detail = None
        for _ in range(5):
            detail = self._request("GET", "/api/v5/trade/order",
                                   {"instId": inst_id(symbol), "ordId": order_id}, signed=True)[0]
            if detail["state"] in ("filled", "canceled"):
                break
            time.sleep(0.5)
        return self._as_binance(symbol, detail)

    # -- backstop: a resting stop order on the exchange ---------------------

    def round_price(self, symbol, price):
        tick = self.symbol_filters(symbol)["tick"]
        decimals = max(0, -int(math.floor(math.log10(tick)))) if tick < 1 else 0
        return f"{math.floor(price / tick) * tick:.{decimals}f}"

    def place_stop(self, symbol, qty, trigger):
        """Rest a conditional market sell of `qty` that fires when the last price
        touches `trigger`. Returns the algo order id."""
        body = {"instId": inst_id(symbol), "tdMode": "cash", "side": "sell", "ordType": "conditional",
                # a spot sell's size is in the base coin; OKX rejects tgtCcy on algo orders
                "sz": self.round_qty(symbol, qty),
                "slTriggerPx": self.round_price(symbol, trigger), "slOrdPx": "-1", "slTriggerPxType": "last"}
        return self._request("POST", "/api/v5/trade/order-algo", body=body, signed=True)[0]["algoId"]

    def cancel_stop(self, symbol, algo_id):
        self._request("POST", "/api/v5/trade/cancel-algos",
                      body=[{"algoId": algo_id, "instId": inst_id(symbol)}], signed=True)

    def stop_status(self, symbol, algo_id):
        """('live' | 'filled' | 'gone', fill in Binance's order shape or None)."""
        d = self._request("GET", "/api/v5/trade/order-algo", {"algoId": algo_id}, signed=True)[0]
        state = d.get("state")
        if state in ("live", "pause", "partially_effective"):
            return "live", None
        if state == "effective" and d.get("ordId"):
            detail = self._request("GET", "/api/v5/trade/order",
                                   {"instId": inst_id(symbol), "ordId": d["ordId"]}, signed=True)[0]
            return "filled", self._as_binance(symbol, detail)
        return "gone", None

    @staticmethod
    def _as_binance(symbol, d):
        qty = float(d.get("accFillSz") or 0)
        avg = float(d.get("avgPx") or 0)
        fee = abs(float(d.get("fee") or 0))
        return {"symbol": symbol, "orderId": d["ordId"],
                "status": "FILLED" if d["state"] == "filled" else d["state"].upper(),
                "executedQty": f"{qty:.8f}", "cummulativeQuoteQty": f"{qty * avg:.8f}",
                "fills": [{"price": f"{avg:.8f}", "qty": f"{qty:.8f}",
                           "commission": f"{fee:.8f}", "commissionAsset": d.get("feeCcy", "")}]
                if qty else []}
