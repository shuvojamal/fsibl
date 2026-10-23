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
        self.algos = {}
        self.frozen = 0.0          # BTC locked by resting stop orders
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
            return ok([{"details": [{"ccy": "USDT", "availBal": str(self.usdt), "cashBal": str(self.usdt)},
                                    {"ccy": "BTC", "availBal": str(self.btc - self.frozen), "cashBal": str(self.btc)}]}])
        if u.path == "/api/v5/trade/order-algo" and method == "POST":
            b = json.loads(body)
            assert b["ordType"] == "conditional" and b["side"] == "sell" and b["slOrdPx"] == "-1"
            if "tgtCcy" in b:   # what real OKX answered on the demo account
                return 400, json.dumps({"code": "51000", "msg": "Parameter tgtCcy error"}).encode()
            aid = f"A{len(self.algos) + 1}"
            self.algos[aid] = {"algoId": aid, "state": "live", "sz": float(b["sz"]), "trigger": float(b["slTriggerPx"])}
            self.frozen += float(b["sz"])
            return ok([{"algoId": aid, "sCode": "0"}])
        if u.path == "/api/v5/trade/cancel-algos":
            for item in json.loads(body):
                a = self.algos[item["algoId"]]
                if a["state"] == "live":
                    a["state"] = "canceled"; self.frozen -= a["sz"]
            return ok([{"sCode": "0"}])
        if u.path == "/api/v5/trade/order-algo" and method == "GET":
            return ok([self.algos[params["algoId"]]])
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
            if qty > self.btc - self.frozen + 1e-9:
                return 200, json.dumps({"code": "1", "msg": "", "data": [
                    {"sCode": "51008", "sMsg": "Insufficient balance (coins frozen)"}]}).encode()
            spend = qty * self.price
            self.btc -= qty
            self.usdt += spend
        self.orders[oid] = {"ordId": oid, "state": "filled", "accFillSz": f"{qty:.8f}",
                            "avgPx": str(self.price), "fee": f"-{spend * 0.001:.8f}", "feeCcy": "USDT"}
        return 200, json.dumps({"code": "0", "msg": "", "data": [{"ordId": oid, "sCode": "0"}]}).encode()


    def fire(self, price):
        """The market trades down to `price`: every resting stop at or above it sells."""
        self.price = price
        for a in self.algos.values():
            if a["state"] == "live" and price <= a["trigger"]:
                self.frozen -= a["sz"]
                _, raw = self._place({"tdMode": "cash", "ordType": "market", "side": "sell", "sz": str(a["sz"])})
                a["state"], a["ordId"] = "effective", json.loads(raw)["data"][0]["ordId"]


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



class BackstopTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.fake = FakeOKX()

    def trader(self):
        return LiveTrader(client(self.fake), ["BTCUSDT"], "1h", Params(fast=3, slow=10, rsi_max=101, take_profit=10),
                          trade_usdt=20, guard_args=(50, 20, os.path.join(self.d, "STOP")), state_dir=self.d,
                          backstop=0.20)

    def buy(self):
        t = self.trader()
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight()
            t.step()
        return t

    def test_backstop_rests_20pct_below_the_stop_and_freezes_the_coins(self):
        t = self.buy()
        pos = t.state["positions"]["BTCUSDT"]
        (algo,) = self.fake.algos.values()
        self.assertEqual(pos["backstop_id"], algo["algoId"])
        self.assertAlmostEqual(algo["trigger"], pos["stop"] * 0.8, delta=0.1)
        self.assertAlmostEqual(algo["sz"], pos["qty"], places=4)
        # frozen coins still count as the position: a restart must not shrink it
        t2 = self.trader()
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t2.preflight()
        self.assertAlmostEqual(t2.state["positions"]["BTCUSDT"]["qty"], pos["qty"])

    def test_raised_stop_moves_the_backstop_up(self):
        t = self.buy()
        pos = t.state["positions"]["BTCUSDT"]
        pos["stop"] *= 1.5
        t._sync_backstops()
        states = [a["state"] for a in self.fake.algos.values()]
        self.assertEqual(states, ["canceled", "live"])
        self.assertAlmostEqual(self.fake.algos["A2"]["trigger"], pos["stop"] * 0.8, delta=0.1)

    def test_fired_backstop_is_booked_as_a_sale_at_the_next_run(self):
        from tradebot.audit import audit
        t = self.buy()
        trigger = self.fake.algos["A1"]["trigger"]
        self.fake.fire(trigger - 1)                 # crash while the bot is not running
        t2 = self.trader()
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):   # same candle: no new signal
            t2.preflight()
            t2.step()
        pos = t2.state["positions"]["BTCUSDT"]
        self.assertEqual(pos["qty"], 0.0)
        self.assertNotIn("backstop_id", pos)
        with open(os.path.join(self.d, "live_trades.csv")) as f:
            self.assertIn(",backstop,", f.read())
        self.assertLess(t2.state["realised"], 0)
        self.assertEqual(audit(self.d), [])

    def test_bot_sale_cancels_the_backstop_first(self):
        t = self.buy()
        pos = t.state["positions"]["BTCUSDT"]
        pos["stop"] = 1e9                           # next candle stops it out
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles(n=321)):
            t.step()
        self.assertEqual(self.fake.algos["A1"]["state"], "canceled")
        self.assertEqual(t.state["positions"]["BTCUSDT"]["qty"], 0.0)
        self.assertAlmostEqual(self.fake.btc, 0.0, places=6)
        self.assertEqual(len(self.fake.algos), 1)   # no new backstop for a closed position



class ManualCloseTests(unittest.TestCase):
    def test_dashboard_sell_closes_cancels_backstop_and_blocks_rebuy(self):
        from tradebot.audit import audit
        d, fake = tempfile.mkdtemp(), FakeOKX()
        mk = lambda **kw: LiveTrader(client(fake), ["BTCUSDT"], "1h",
                                     Params(fast=3, slow=10, rsi_max=101, take_profit=10), trade_usdt=20,
                                     guard_args=(50, 20, os.path.join(d, "STOP")), state_dir=d, backstop=0.2, **kw)
        t = mk()
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight(); t.step()
        fake.price = 110.0
        t2 = mk(close_now=["btcusdt"])
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles(n=321)):
            t2.preflight(); t2.step()           # the new candle would signal a buy again
        self.assertEqual(t2.state["positions"]["BTCUSDT"]["qty"], 0.0)
        self.assertEqual(fake.algos["A1"]["state"], "canceled")
        with open(os.path.join(d, "live_trades.csv")) as f:
            rows = f.read().splitlines()
        self.assertEqual([r.split(",")[2] for r in rows[1:]], ["BUY", "SELL"])   # no re-buy
        self.assertIn(",manual,", rows[2])
        self.assertGreater(t2.state["realised"], 0)
        self.assertEqual(audit(d), [])


if __name__ == "__main__":
    unittest.main()
