"""Re-buy wait follows the current setting, and a held-back buy is retried the same day."""
import os
import tempfile
import time
import unittest
from unittest import mock

from tradebot.live import LiveTrader
from tradebot.strategy import Params
from tests.test_live import FakeBinance, client, trending_candles


class RebuyTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.fake = FakeBinance(price=100.0)

    def trader(self, **kw):
        return LiveTrader(client(self.fake), ["BTCUSDT"], "1h", Params(fast=3, slow=10, rsi_max=101, take_profit=10),
                          trade_usdt=20, guard_args=(50, 20, os.path.join(self.dir, "STOP")), state_dir=self.dir,
                          max_price_gap=0.0, **kw)

    def run_step(self, t):
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight()
            t.step()

    def test_wait_set_to_zero_buys_on_the_same_candle(self):
        t = self.trader(rebuy_block_days=7)
        t.state["sold_by_hand"] = {"BTCUSDT": time.time() * 1000 - 86_400_000}   # sold by hand yesterday
        t._save()
        self.run_step(t)
        self.assertEqual(self.fake.orders, [])                # held back by the 7-day wait
        self.run_step(self.trader(rebuy_block_days=0))        # owner sets the wait to 0, same daily candle
        self.assertEqual([o["side"] for o in self.fake.orders], ["BUY"])

    def test_old_block_records_follow_the_new_setting(self):
        t = self.trader(rebuy_block_days=3)
        t.state["rebuy_blocked"] = {"BTCUSDT": time.time() * 1000 + 3 * 86_400_000}   # 7-day block set 4 days ago
        t._save()
        self.run_step(t)
        self.assertEqual([o["side"] for o in self.fake.orders], ["BUY"])

    def test_runs_from_before_the_fix_are_caught_up(self):
        t = self.trader(rebuy_block_days=7)
        t.state["rebuy_blocked"] = {"BTCUSDT": time.time() * 1000 + 6 * 86_400_000}   # old-style record
        t._save()
        self.run_step(t)
        self.assertEqual(self.fake.orders, [])
        t = self.trader(rebuy_block_days=0)
        t.state["positions"]["BTCUSDT"].pop("retry_candle", None)   # an old run never marked it
        t._save()
        self.run_step(t)
        self.assertEqual([o["side"] for o in self.fake.orders], ["BUY"])
        self.run_step(self.trader(rebuy_block_days=0))
        self.assertEqual(len(self.fake.orders), 1)

    def test_paused_then_resumed_same_day(self):
        self.run_step(self.trader(pause_entries=True))
        self.assertEqual(self.fake.orders, [])
        self.run_step(self.trader())
        self.assertEqual([o["side"] for o in self.fake.orders], ["BUY"])

    def test_no_repeat_buy_after_the_retry(self):
        self.run_step(self.trader(pause_entries=True))
        self.run_step(self.trader())
        self.run_step(self.trader())
        self.assertEqual(len(self.fake.orders), 1)


if __name__ == "__main__":
    unittest.main()


class ReportSettingTests(unittest.TestCase):
    def test_report_uses_the_accounts_checks_setting(self):
        import io, json, sys
        from contextlib import redirect_stdout
        from tests.test_opportunity import uptrend
        from tradebot import cli
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "settings.json"), "w") as f:
            json.dump({"min_score": 6}, f)
        out = io.StringIO()
        with mock.patch("tradebot.report.fetch_candles", return_value=uptrend()), \
                mock.patch.object(sys, "argv", ["tradebot", "report", "BTCUSDT", "--exchange", "none", "--state-dir", d]), \
                redirect_stdout(out):
            cli.main()
        self.assertIn("need 6 of 8", out.getvalue())


class RoundQtyTests(unittest.TestCase):
    """2026-11-11: 0.206 ZEC was sold as 0.205 (float error), leaving dust and failing the audit."""

    def check(self, client):
        client.symbol_filters = lambda sym: {"step": 0.001, "min_qty": 0.001, "tick": 0.01, "min_notional": 5}
        self.assertEqual(client.round_qty("ZECUSDT", 0.206), "0.206")
        self.assertEqual(client.round_qty("ZECUSDT", 0.043), "0.043")
        self.assertEqual(client.round_qty("ZECUSDT", 0.2059), "0.205")      # still rounds down
        client.symbol_filters = lambda sym: {"step": 0.00001, "min_qty": 0.00001, "tick": 0.01, "min_notional": 5}
        bad = [k for k in range(1, 5000) if client.round_qty("X", round(k * 0.00001, 8)) != f"{k * 0.00001:.5f}"]
        self.assertEqual(bad, [])

    def test_binance(self):
        from tradebot.binance_client import BinanceClient
        self.check(BinanceClient("k", "s"))

    def test_okx(self):
        from tradebot.okx_client import OKXClient
        self.check(OKXClient(api_key="k", api_secret="s", passphrase="p"))
