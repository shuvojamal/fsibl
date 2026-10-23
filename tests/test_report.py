import json
import os
import tempfile
import unittest
from unittest import mock

from tests.test_live import SECRET, FakeBinance
from tests.test_opportunity import uptrend
from tradebot.binance_client import BinanceClient
from tradebot.report import fills_summary, report


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        with open(os.path.join(self.dir, "live_state.json"), "w") as f:
            json.dump({"positions": {
                "BTCUSDT": {"qty": 0.002, "entry": 40000.0, "stop": 38000.0, "target": 1e9, "last_candle": 0},
                "ETHUSDT": {"qty": 0.0, "entry": 0.0, "stop": 0.0, "target": 0.0, "last_candle": 0}}}, f)
        with open(os.path.join(self.dir, "live_trades.csv"), "w") as f:
            f.write("time,symbol,side,qty,price,fee,reason,pnl_usdt,order_id\n"
                    "2026-10-22 10:00:00 UTC,ETHUSDT,BUY,0.1,2000,0.2,signal,,1\n"
                    "2026-10-22 12:00:00 UTC,ETHUSDT,SELL,0.1,2100,0.21,stop_loss,+9.59,2\n")

    def test_report_lists_positions_pnl_trades_and_scores(self):
        fake = FakeBinance(price=50000.0, usdt=900.0)
        client = BinanceClient("key", SECRET.decode(), transport=fake)
        with mock.patch("tradebot.report.fetch_candles", return_value=uptrend()):
            lines = report(client, self.dir, ["BTCUSDT", "ETHUSDT"])
        text = "\n".join(lines)
        self.assertIn("free USDT: 900.00", text)
        self.assertIn("open positions: 1", text)
        self.assertIn("+20.00", text)            # (50000-40000)*0.002 unrealised
        self.assertIn("+25.00%", text)
        self.assertIn("closed trades: 1, realised P&L: +9.59 USDT", text)
        self.assertIn("IN BTCUSDT", text)        # held position flagged in the score table
        self.assertRegex(text, r"ETHUSDT +\d/8")

    def test_report_without_account(self):
        with mock.patch("tradebot.report.fetch_candles", return_value=uptrend()):
            lines = report(None, self.dir, ["BTCUSDT"])
        self.assertNotIn("free USDT", "\n".join(lines))
        self.assertIn("open positions: 1", "\n".join(lines))


if __name__ == "__main__":
    unittest.main()


class FillsSummaryTests(unittest.TestCase):
    def test_summarises_slippage_and_fees_per_side(self):
        d = tempfile.mkdtemp()
        self.assertEqual(fills_summary(d), [])
        with open(os.path.join(d, "fills.csv"), "w") as f:
            f.write("time,symbol,side,signal_price,fill_price,slippage_pct,fee_pct\n"
                    "t1,BTCUSDT,BUY,100,100.1,0.1000,0.1000\n"
                    "t2,ETHUSDT,BUY,10,10.03,0.3000,0.1000\n"
                    "t3,BTCUSDT,SELL,110,109.89,0.1000,0.1000\n")
        out = "\n".join(fills_summary(d))
        self.assertIn("3 fills", out)
        self.assertIn("BUY    2 fills  avg slippage +0.200%  worst +0.300%", out)
        self.assertIn("SELL   1 fills", out)
