"""Exercise the signed client and the live trader against an in-memory fake exchange."""
import hashlib
import hmac
import json
import os
import tempfile
import unittest
import urllib.parse
from unittest import mock

from tradebot.binance_client import BinanceClient, BinanceError, fill_summary
from tradebot.data import Candle
from tradebot.live import LiveTrader, RiskGuard
from tradebot.strategy import Params

SECRET = b"topsecret"


class FakeBinance:
    """Enough of the Spot API to buy and sell BTCUSDT at a fixed price."""

    def __init__(self, price=50000.0, usdt=1000.0):
        self.price, self.usdt, self.btc = price, usdt, 0.0
        self.orders = []

    def __call__(self, method, url, headers, body):
        u = urllib.parse.urlparse(url)
        params = dict(urllib.parse.parse_qsl(body.decode() if body else u.query))
        if u.path in ("/api/v3/account", "/api/v3/order", "/api/v3/order/test"):
            assert headers.get("X-MBX-APIKEY") == "key", "missing api key header"
            sig = params.pop("signature")
            expect = hmac.new(SECRET, urllib.parse.urlencode(params).encode(), hashlib.sha256).hexdigest()
            if sig != expect:
                return 401, json.dumps({"code": -1022, "msg": "bad signature"}).encode()
        if u.path == "/api/v3/time":
            return 200, json.dumps({"serverTime": 1_700_000_000_000}).encode()
        if u.path == "/api/v3/ticker/price":
            return 200, json.dumps({"price": str(self.price)}).encode()
        if u.path == "/api/v3/exchangeInfo":
            return 200, json.dumps({"symbols": [{"filters": [
                {"filterType": "LOT_SIZE", "stepSize": "0.00001", "minQty": "0.00001"},
                {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
                {"filterType": "NOTIONAL", "minNotional": "5"}]}]}).encode()
        if u.path == "/api/v3/account":
            return 200, json.dumps({"balances": [{"asset": "USDT", "free": str(self.usdt)},
                                                 {"asset": "BTC", "free": str(self.btc)}]}).encode()
        if u.path == "/api/v3/order":
            return self._order(params)
        return 404, json.dumps({"code": -1, "msg": "unknown"}).encode()

    def _order(self, p):
        self.orders.append(p)
        if p["side"] == "BUY":
            spend = float(p["quoteOrderQty"])
            if spend > self.usdt:
                return 400, json.dumps({"code": -2010, "msg": "insufficient balance"}).encode()
            qty = spend / self.price
            self.usdt -= spend
            self.btc += qty * 0.999
        else:
            qty = float(p["quantity"])
            if qty > self.btc + 1e-9:
                return 400, json.dumps({"code": -2010, "msg": "insufficient balance"}).encode()
            spend = qty * self.price
            self.btc -= qty
            self.usdt += spend * 0.999
        return 200, json.dumps({
            "symbol": "BTCUSDT", "orderId": len(self.orders), "status": "FILLED",
            "executedQty": f"{qty:.8f}", "cummulativeQuoteQty": f"{spend:.8f}",
            "fills": [{"price": str(self.price), "qty": f"{qty:.8f}",
                       "commission": f"{spend * 0.001:.8f}", "commissionAsset": "USDT"}]}).encode()


def client(fake):
    return BinanceClient("key", SECRET.decode(), transport=fake)


class ClientTests(unittest.TestCase):
    def test_signed_request_is_accepted(self):
        self.assertEqual(client(FakeBinance()).balances()["USDT"], 1000.0)

    def test_wrong_secret_is_rejected(self):
        c = BinanceClient("key", "wrong", transport=FakeBinance())
        with self.assertRaises(BinanceError):
            c.balances()

    def test_missing_keys_fail_before_any_request(self):
        c = BinanceClient("", "", transport=lambda *a: self.fail("should not call out"))
        with self.assertRaises(BinanceError):
            c.balances()

    def test_qty_rounds_down_to_lot_step(self):
        self.assertEqual(client(FakeBinance()).round_qty("BTCUSDT", 0.123456789), "0.12345")

    def test_fill_summary(self):
        fake = FakeBinance()
        order = client(fake).market_order("BTCUSDT", "BUY", quote_qty=100)
        qty, avg, fee = fill_summary(order)
        self.assertAlmostEqual(qty, 0.002)
        self.assertAlmostEqual(avg, 50000.0)
        self.assertAlmostEqual(fee, 0.1)

    def test_fill_summary_nets_out_fee_taken_in_the_coin(self):
        # Seen on OKX demo: a 0.00024421 BTC buy charged 0.00000024 BTC in fee,
        # so only 0.00024397 BTC arrived; selling the gross amount comes up short.
        order = {"symbol": "BTCUSDT", "executedQty": "0.00024421",
                 "cummulativeQuoteQty": "20.0", "fills": [
                     {"price": "81896.5", "qty": "0.00024421",
                      "commission": "0.00000024", "commissionAsset": "BTC"}]}
        qty, avg, fee = fill_summary(order)
        self.assertAlmostEqual(qty, 0.00024397)
        self.assertAlmostEqual(fee, 0.00000024 * 81896.5)


def trending_candles(n=320, k=2):
    """Down-trend, then a sharp rally whose EMA crossover lands on the last candle."""
    closes = [100 - i * 0.2 for i in range(n - k)] + [100 - (n - k) * 0.2 + i * 2 for i in range(k)]
    out, prev = [], closes[0]
    for i, c in enumerate(closes):
        out.append(Candle(i * 3600_000, prev, max(prev, c), min(prev, c), c, 1.0, (i + 1) * 3600_000 - 1))
        prev = c
    return out


class LiveTraderTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.fake = FakeBinance(price=100.0)
        self.params = Params(fast=3, slow=10, rsi_max=101, take_profit=10)

    def trader(self, **kw):
        args = dict(trade_usdt=20, guard_args=(50, 20, os.path.join(self.dir, "STOP")),
                    state_dir=self.dir)
        args.update(kw)
        return LiveTrader(client(self.fake), ["BTCUSDT"], "1h", self.params, **args)

    def test_buy_signal_places_market_order_and_persists(self):
        t = self.trader()
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight()
            t.step()
        self.assertEqual(len(self.fake.orders), 1)
        self.assertEqual(self.fake.orders[0]["side"], "BUY")
        with open(os.path.join(self.dir, "live_state.json")) as f:
            self.assertGreater(json.load(f)["positions"]["BTCUSDT"]["qty"], 0)

    def test_same_candle_does_not_trade_twice(self):
        t = self.trader()
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight()
            t.step()
            t.step()
        self.assertEqual(len(self.fake.orders), 1)

    def test_dry_run_never_orders(self):
        t = self.trader(dry_run=True)
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight()
            t.step()
        self.assertEqual(self.fake.orders, [])

    def test_kill_switch_blocks_buy(self):
        t = self.trader()
        open(os.path.join(self.dir, "STOP"), "w").close()
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight()
            t.step()
        self.assertEqual(self.fake.orders, [])

    def test_trade_size_above_cap_is_refused(self):
        t = self.trader(trade_usdt=60)
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight()
            t.step()
        self.assertEqual(self.fake.orders, [])

    def test_restart_adopts_coins_already_on_exchange(self):
        self.fake.btc = 0.5
        t = self.trader()
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight()
        self.assertEqual(t.state["positions"]["BTCUSDT"]["qty"], 0.5)

    def test_max_open_cap_blocks_new_buys(self):
        t = self.trader(max_open=1)
        t.state["positions"]["ETHUSDT"] = {"qty": 1.0, "entry": 100.0, "stop": 90.0,
                                           "target": 1e9, "last_candle": 0}
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight()
            t.step()
        self.assertEqual(self.fake.orders, [])  # BTC buy signal, but one slot and it's taken

    def test_no_adopt_leaves_existing_coins_alone(self):
        self.fake.btc = 0.5
        t = self.trader(adopt=False)
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight()
        self.assertEqual(t.state["positions"]["BTCUSDT"]["qty"], 0.0)


class RiskSizedLiveTests(unittest.TestCase):
    """The opportunity engine sizes each buy from the whole account, not the per-trade cap."""

    def test_spend_is_risk_fraction_of_account_equity(self):
        from tradebot.engines import OpportunityEngine
        from tradebot.opportunity import OppParams
        from tests.test_opportunity import uptrend
        fake = FakeBinance(usdt=1000.0)
        d = tempfile.mkdtemp()
        engine = OpportunityEngine(OppParams(min_score=0, risk_frac=0.01))
        t = LiveTrader(client(fake), ["BTCUSDT"], "1d", Params(), trade_usdt=5000,
                       guard_args=(5000, 1000, os.path.join(d, "STOP")), state_dir=d, engine=engine)
        candles = uptrend()
        action = engine.decide(candles, in_position=False)
        price, stop = candles[-1].close, action[1].stop
        with mock.patch("tradebot.live.fetch_candles", return_value=candles):
            t.preflight()
            t.step()
        self.assertEqual(len(fake.orders), 1)
        spent = float(fake.orders[0]["quoteOrderQty"])
        expected = 1000.0 * 0.01 / (price - stop) * price  # lose 1% of 1000 USDT at the stop
        self.assertAlmostEqual(spent, expected, places=1)

    def test_per_trade_size_caps_the_risk_sizing(self):
        from tradebot.engines import OpportunityEngine
        from tradebot.opportunity import OppParams
        from tests.test_opportunity import uptrend
        fake = FakeBinance(usdt=1000.0)
        d = tempfile.mkdtemp()
        engine = OpportunityEngine(OppParams(min_score=0, risk_frac=0.01))
        t = LiveTrader(client(fake), ["BTCUSDT"], "1d", Params(), trade_usdt=30,
                       guard_args=(50, 1000, os.path.join(d, "STOP")), state_dir=d, engine=engine)
        with mock.patch("tradebot.live.fetch_candles", return_value=uptrend()):
            t.preflight()
            t.step()
        self.assertEqual(float(fake.orders[0]["quoteOrderQty"]), 30.0)


class SlotPriorityTests(unittest.TestCase):
    def test_highest_score_gets_the_last_free_slot(self):
        from tradebot.opportunity import Plan

        class FixedEngine:
            history = 50
            scores = {"BTCUSDT": 5, "ETHUSDT": 7}

            def decide(self, candles, in_position):
                return ("buy", Plan(candles[-1].close * 0.9, 1e12, self.sym_score, ["x"]))

        engine = FixedEngine()
        fake = FakeBinance(price=100.0)
        d = tempfile.mkdtemp()
        t = LiveTrader(client(fake), ["BTCUSDT", "ETHUSDT"], "1d", Params(), trade_usdt=20,
                       guard_args=(50, 20, os.path.join(d, "STOP")), state_dir=d,
                       engine=engine, max_open=1)

        def fetch(sym, interval, n):
            engine.sym_score = engine.scores[sym]
            return trending_candles()

        with mock.patch("tradebot.live.fetch_candles", side_effect=fetch):
            t.preflight()
            t.step()
        self.assertEqual(len(fake.orders), 1)
        self.assertEqual(fake.orders[0]["symbol"], "ETHUSDT")  # score 7 beats score 5


class RiskGuardTests(unittest.TestCase):
    def test_daily_loss_limit(self):
        g = RiskGuard(50, 20, "/nonexistent/STOP", {})
        self.assertTrue(g.can_open(10)[0])
        g.record(-25)
        self.assertFalse(g.can_open(10)[0])
        self.assertTrue(g.can_close()[0])


if __name__ == "__main__":
    unittest.main()
