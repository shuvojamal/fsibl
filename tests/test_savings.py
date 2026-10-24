"""Auto savings: spare USDT in Binance flexible savings, taken out for buys (research round 32)."""
import json
import os
import tempfile
import unittest
import urllib.parse
from unittest import mock

from tradebot.binance_client import LIVE_URL, BinanceClient
from tradebot.control import live_args, read_controls
from tradebot.live import LiveTrader
from tradebot.strategy import Params
from tests.test_live import SECRET, FakeBinance, trending_candles


class FakeEarn(FakeBinance):
    """FakeBinance plus the Simple Earn flexible endpoints."""

    def __init__(self, saved=0.0, fail=False, **kw):
        super().__init__(**kw)
        self.saved, self.fail, self.earn_calls = saved, fail, []

    def __call__(self, method, url, headers, body):
        u = urllib.parse.urlparse(url)
        if not u.path.startswith("/sapi/v1/simple-earn/"):
            return super().__call__(method, url, headers, body)
        p = dict(urllib.parse.parse_qsl(body.decode() if body else u.query))
        assert "signature" in p and headers.get("X-MBX-APIKEY") == "key"
        if self.fail:
            return 400, json.dumps({"code": -6003, "msg": "permission denied"}).encode()
        path = u.path.rsplit("/", 1)[1]
        self.earn_calls.append((path, p.get("amount")))
        if path == "list":
            return 200, json.dumps({"rows": [{"asset": "USDT", "productId": "USDT001", "canPurchase": True,
                                              "canRedeem": True, "minPurchaseAmount": "0.1",
                                              "latestAnnualPercentageRate": "0.04"}], "total": 1}).encode()
        if path == "position":
            return 200, json.dumps({"rows": [{"asset": "USDT", "productId": "USDT001",
                                              "totalAmount": f"{self.saved:.8f}"}] if self.saved else [],
                                    "total": 1}).encode()
        amt = float(p["amount"])
        if path == "subscribe":
            if amt > self.usdt + 1e-9:
                return 400, json.dumps({"code": -6012, "msg": "insufficient"}).encode()
            self.usdt -= amt; self.saved += amt
            return 200, json.dumps({"purchaseId": 1, "success": True}).encode()
        if path == "redeem":
            amt = min(amt, self.saved)
            self.saved -= amt; self.usdt += amt
            return 200, json.dumps({"redeemId": 1, "success": True}).encode()
        return 404, b"{}"


class SavingsTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.params = Params(fast=3, slow=10, rsi_max=101, take_profit=10)

    def trader(self, fake, live=True, **kw):
        c = BinanceClient("key", SECRET.decode(), transport=fake, base_url=LIVE_URL if live else
                          "https://testnet.binance.vision")
        args = dict(trade_usdt=20, guard_args=(50, 20, os.path.join(self.dir, "STOP")), state_dir=self.dir,
                    max_price_gap=0.0)
        args.update(kw)
        return LiveTrader(c, ["BTCUSDT"], "1h", self.params, **args)

    def run_step(self, t, candles):
        with mock.patch("tradebot.live.fetch_candles", return_value=candles), mock.patch("tradebot.live.time.sleep"):
            t.preflight()
            t.step()

    def test_buy_takes_cash_out_of_savings_and_spare_goes_back(self):
        fake = FakeEarn(price=100.0, usdt=0.0, saved=1000.0)
        t = self.trader(fake, savings=True)
        self.run_step(t, trending_candles())
        self.assertEqual(fake.orders[0]["side"], "BUY")
        self.assertEqual(float(fake.orders[0]["quoteOrderQty"]), 20.0)
        self.assertEqual([c[0] for c in fake.earn_calls if c[0] in ("redeem", "subscribe")], ["redeem"])
        self.assertLess(fake.usdt, 1.0)               # only what the buy needed came out
        self.assertAlmostEqual(fake.saved + fake.usdt + 20, 1000.0, places=1)
        self.assertGreater(json.load(open(os.path.join(self.dir, "live_state.json")))["savings"]["balance"], 900)

    def test_spot_cash_used_first_without_redeeming(self):
        fake = FakeEarn(price=100.0, usdt=500.0)
        t = self.trader(fake, savings=True)
        self.run_step(t, trending_candles())
        self.assertNotIn("redeem", [c[0] for c in fake.earn_calls])
        self.assertAlmostEqual(fake.saved, 480.0, places=1)

    def test_keep_amount_stays_on_spot(self):
        fake = FakeEarn(price=100.0, usdt=500.0)
        t = self.trader(fake, savings=True, savings_keep=50.0)
        self.run_step(t, trending_candles(k=0))        # no signal, just the sweep
        self.assertAlmostEqual(fake.usdt, 50.0, places=1)

    def test_dry_run_moves_nothing(self):
        fake = FakeEarn(price=100.0, usdt=500.0)
        t = self.trader(fake, savings=True, dry_run=True)
        self.run_step(t, trending_candles())
        self.assertEqual(fake.orders, [])
        self.assertNotIn("subscribe", [c[0] for c in fake.earn_calls])
        self.assertEqual(fake.usdt, 500.0)

    def test_ignored_on_testnet(self):
        fake = FakeEarn(price=100.0, usdt=500.0)
        t = self.trader(fake, live=False, savings=True)
        self.run_step(t, trending_candles())
        self.assertEqual(fake.earn_calls, [])
        self.assertEqual(len(fake.orders), 1)

    def test_savings_error_never_blocks_trading(self):
        fake = FakeEarn(price=100.0, usdt=500.0, fail=True)
        t = self.trader(fake, savings=True)
        self.run_step(t, trending_candles())
        self.assertEqual(len(fake.orders), 1)
        self.assertEqual(fake.orders[0]["side"], "BUY")

    def test_switching_off_moves_the_bots_deposits_back(self):
        fake = FakeEarn(price=100.0, usdt=500.0, saved=200.0)   # 200 were the owner's own
        self.run_step(self.trader(fake, savings=True), trending_candles(k=0))
        self.assertAlmostEqual(fake.saved, 700.0, places=1)
        self.run_step(self.trader(fake, savings=False), trending_candles(k=0))
        self.assertAlmostEqual(fake.saved, 200.0, places=1)    # the owner's own savings untouched
        self.assertAlmostEqual(fake.usdt, 500.0, places=1)

    def test_equity_without_capital_counts_savings(self):
        fake = FakeEarn(price=100.0, usdt=100.0, saved=900.0)
        t = self.trader(fake, savings=True)
        self.assertAlmostEqual(t._equity(), 1000.0, places=2)


class SavingsControlTests(unittest.TestCase):
    def test_flag_only_when_true(self):
        d = tempfile.mkdtemp()
        for raw, want in ((True, True), ("yes", False), (None, False)):
            with open(os.path.join(d, "settings.json"), "w") as f:
                json.dump({} if raw is None else {"savings": raw}, f)
            self.assertEqual("--savings" in live_args(read_controls(d)), want)


if __name__ == "__main__":
    unittest.main()


class IgnoreTrendTests(unittest.TestCase):
    """Round 33: the 200-day trend check can be made to always count as passed."""

    def test_ignored_check_always_passes(self):
        from tests.test_opportunity import uptrend
        from tradebot.opportunity import Opportunity, OppParams
        cs = uptrend()
        down = [type(c)(c.open_time, 1e6 - c.open, 1e6 - c.low, 1e6 - c.high, 1e6 - c.close, c.volume, c.close_time)
                for c in cs]                       # mirrored: price far below a falling 200-day average
        i = len(down) - 1
        self.assertFalse(dict(Opportunity(OppParams()).prepare(down).checks(i))["trend_up"])
        self.assertTrue(dict(Opportunity(OppParams(ignore=("trend_up",))).prepare(down).checks(i))["trend_up"])

    def test_setting_maps_to_flag(self):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "settings.json"), "w") as f:
            json.dump({"ignore_trend": True}, f)
        args = live_args(read_controls(d))
        self.assertEqual(args[args.index("--ignore-check") + 1], "trend_up")
        with open(os.path.join(d, "settings.json"), "w") as f:
            json.dump({"ignore_trend": "yes"}, f)
        self.assertNotIn("--ignore-check", live_args(read_controls(d)))
