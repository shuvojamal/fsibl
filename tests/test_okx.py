"""The OKX client against an in-memory fake that checks V5 request signing."""
import base64
import hashlib
import hmac
import json
import os
import tempfile
import unittest
import urllib.parse
from unittest import mock

from tradebot.binance_client import BinanceError, fill_summary
from tradebot.live import LiveTrader
from tradebot.okx_client import OKXClient, inst_id
from tradebot.strategy import Params
from tests.test_live import trending_candles

SECRET = b"okxsecret"


class FakeOKX:
    def __init__(self, price=100.0, usdt=1000.0):
        self.price, self.usdt, self.btc = price, usdt, 0.0
        self.orders = {}
        self.saw_demo_header = None

    def __call__(self, method, url, headers, body):
        u = urllib.parse.urlparse(url)
        request_path = u.path + ("?" + u.query if u.query else "")
        params = dict(urllib.parse.parse_qsl(u.query))
        self.saw_demo_header = headers.get("x-simulated-trading")
        if u.path.startswith(("/api/v5/account", "/api/v5/trade")):
            msg = headers["OK-ACCESS-TIMESTAMP"] + method + request_path + (body.decode() if body else "")
            expect = base64.b64encode(hmac.new(SECRET, msg.encode(), hashlib.sha256).digest()).decode()
            if headers.get("OK-ACCESS-SIGN") != expect or headers.get("OK-ACCESS-PASSPHRASE") != "pass":
                return 401, json.dumps({"code": "50113", "msg": "Invalid Sign"}).encode()
        ok = lambda data: (200, json.dumps({"code": "0", "msg": "", "data": data}).encode())
        if u.path == "/api/v5/public/time":
            return ok([{"ts": "1700000000000"}])
        if u.path == "/api/v5/market/ticker":
            return ok([{"last": str(self.price)}])
        if u.path == "/api/v5/public/instruments":
            return ok([{"lotSz": "0.00001", "minSz": "0.00001", "tickSz": "0.1"}])
        if u.path == "/api/v5/account/balance":
            return ok([{"details": [{"ccy": "USDT", "availBal": str(self.usdt)},
                                    {"ccy": "BTC", "availBal": str(self.btc)}]}])
        if u.path == "/api/v5/trade/order" and method == "POST":
            return self._place(json.loads(body))
        if u.path == "/api/v5/trade/order" and method == "GET":
            return ok([self.orders[params["ordId"]]])
        return 404, json.dumps({"code": "1", "msg": "unknown"}).encode()

    def _place(self, b):
        assert b["tdMode"] == "cash" and b["ordType"] == "market"
        oid = str(len(self.orders) + 1)
        if b["side"] == "buy":
            spend = float(b["sz"])
            assert b["tgtCcy"] == "quote_ccy"
            if spend > self.usdt:
                return 200, json.dumps({"code": "1", "msg": "", "data": [
                    {"sCode": "51008", "sMsg": "Insufficient balance"}]}).encode()
            qty = spend / self.price
            self.usdt -= spend
            self.btc += qty
        else:
            qty = float(b["sz"])
            spend = qty * self.price
            self.btc -= qty
            self.usdt += spend
        self.orders[oid] = {"ordId": oid, "state": "filled", "accFillSz": f"{qty:.8f}",
                            "avgPx": str(self.price), "fee": f"-{spend * 0.001:.8f}", "feeCcy": "USDT"}
        return 200, json.dumps({"code": "0", "msg": "", "data": [{"ordId": oid, "sCode": "0"}]}).encode()


def client(fake, demo=True):
    return OKXClient("key", SECRET.decode(), "pass", demo=demo, transport=fake)


class OKXClientTests(unittest.TestCase):
    def test_inst_id(self):
        self.assertEqual(inst_id("BTCUSDT"), "BTC-USDT")
        self.assertEqual(inst_id("SOLUSDT"), "SOL-USDT")

    def test_signed_request_accepted_and_demo_header_sent(self):
        fake = FakeOKX()
        self.assertEqual(client(fake).balances()["USDT"], 1000.0)
        self.assertEqual(fake.saw_demo_header, "1")

    def test_live_mode_omits_demo_header(self):
        fake = FakeOKX()
        client(fake, demo=False).balances()
        self.assertIsNone(fake.saw_demo_header)

    def test_bad_passphrase_rejected(self):
        c = OKXClient("key", SECRET.decode(), "wrong", transport=FakeOKX())
        with self.assertRaises(BinanceError):
            c.balances()

    def test_market_buy_returns_binance_shaped_fill(self):
        fake = FakeOKX()
        order = client(fake).market_order("BTCUSDT", "BUY", quote_qty=50)
        qty, avg, fee = fill_summary(order)
        self.assertAlmostEqual(qty, 0.5)
        self.assertAlmostEqual(avg, 100.0)
        self.assertAlmostEqual(fee, 0.05)
        self.assertEqual(order["status"], "FILLED")

    def test_insufficient_balance_surfaces_okx_reason(self):
        with self.assertRaises(BinanceError) as cm:
            client(FakeOKX(usdt=10)).market_order("BTCUSDT", "BUY", quote_qty=50)
        self.assertIn("Insufficient", str(cm.exception))


class UnlistedSymbolTests(unittest.TestCase):
    def test_preflight_skips_a_coin_the_exchange_does_not_list(self):
        fake = FakeOKX()
        real = fake.__call__

        def transport(method, url, headers, body):
            if "instruments" in url and "ZEC-USDT" in url:
                return 200, json.dumps({"code": "51001", "msg": "Instrument ID doesn't exist.",
                                        "data": []}).encode()
            return real(method, url, headers, body)

        d = tempfile.mkdtemp()
        t = LiveTrader(client(transport), ["ZECUSDT", "BTCUSDT"], "1h",
                       Params(fast=3, slow=10, rsi_max=101, take_profit=10), trade_usdt=20,
                       guard_args=(50, 20, os.path.join(d, "STOP")), state_dir=d)
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight()
            t.step()
        self.assertEqual(t.symbols, ["BTCUSDT"])
        self.assertEqual(len(fake.orders), 1)  # BTC still traded


class LiveTraderOnOKXTests(unittest.TestCase):
    def test_full_cycle_on_okx(self):
        fake = FakeOKX()
        d = tempfile.mkdtemp()
        t = LiveTrader(client(fake), ["BTCUSDT"], "1h",
                       Params(fast=3, slow=10, rsi_max=101, take_profit=10), trade_usdt=20,
                       guard_args=(50, 20, os.path.join(d, "STOP")), state_dir=d)
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight()
            t.step()
        self.assertEqual(len(fake.orders), 1)
        self.assertAlmostEqual(fake.btc, 0.2)
        self.assertGreater(t.state["positions"]["BTCUSDT"]["qty"], 0)


if __name__ == "__main__":
    unittest.main()
