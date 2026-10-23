import csv
import json
import os
import tempfile
import unittest
from unittest import mock

from tradebot.audit import audit
from tradebot.live import LiveTrader
from tradebot.strategy import Params
from tests.test_live import FakeBinance, client, trending_candles

HEAD = ["time", "symbol", "side", "qty", "price", "fee", "reason", "pnl_usdt", "order_id"]


def write(d, positions, trades=(), realised=0.0, equity_open=None):
    json.dump({"positions": positions, "realised": realised}, open(os.path.join(d, "live_state.json"), "w"))
    with open(os.path.join(d, "live_trades.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(HEAD)
        for t in trades:
            w.writerow(t)
    if equity_open is None:
        if os.path.exists(os.path.join(d, "equity.csv")):
            os.remove(os.path.join(d, "equity.csv"))
    else:
        with open(os.path.join(d, "equity.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["time", "equity", "realised", "open_positions"])
            w.writerow(["2026-10-23 00:07:00 UTC", "5000.00", f"{realised:.2f}", equity_open])


BTC = {"qty": 0.5, "entry": 100.0, "stop": 90.0, "target": 1e9, "peak": 110.0}
BUY = ["2026-10-22 00:07:00 UTC", "BTCUSDT", "BUY", 0.5, 100, 0.05, "signal", "", 1]


class Audit(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def test_consistent_state_passes(self):
        write(self.d, {"BTCUSDT": BTC, "ETHUSDT": {"qty": 0.0, "entry": 0.0, "stop": 0.0}}, [BUY], equity_open=1)
        self.assertEqual(audit(self.d, max_open=5), [])

    def test_partial_sell_leaving_coins_behind_is_flagged(self):
        sell = ["2026-10-23 00:07:00 UTC", "BTCUSDT", "SELL", 0.4, 95, 0.04, "stop_loss", "-2.0400", 2]
        write(self.d, {"BTCUSDT": {**BTC, "qty": 0.0}}, [BUY, sell], realised=-2.04)
        self.assertTrue(any("nets to 0.1" in p for p in audit(self.d)))

    def test_stop_above_highest_price_is_flagged(self):
        write(self.d, {"BTCUSDT": {**BTC, "stop": 120.0}}, [BUY])
        self.assertTrue(any("stop 120" in p for p in audit(self.d)))

    def test_too_many_positions_and_realised_mismatch_are_flagged(self):
        write(self.d, {"BTCUSDT": BTC}, [BUY], realised=5.0, equity_open=3)
        problems = audit(self.d, max_open=0)
        self.assertTrue(any("realised" in p for p in problems))
        self.assertTrue(any("says 3 open" in p for p in problems))
        eth = {**BTC, "qty": 1.0}
        buy_eth = ["2026-10-22 00:07:01 UTC", "ETHUSDT", "BUY", 1.0, 100, 0.1, "signal", "", 3]
        write(self.d, {"BTCUSDT": BTC, "ETHUSDT": eth}, [BUY, buy_eth])
        self.assertTrue(any("cap of 1" in p for p in audit(self.d, max_open=1)))
        self.assertEqual(audit(self.d, max_open=2), [])

    def test_missing_state_is_flagged(self):
        self.assertTrue(audit(self.d)[0].endswith("missing"))

    def test_real_trader_output_passes(self):
        fake = FakeBinance(price=100.0)
        t = LiveTrader(client(fake), ["BTCUSDT"], "1h", Params(fast=3, slow=10, rsi_max=101, take_profit=10),
                       trade_usdt=20, guard_args=(50, 20, os.path.join(self.d, "STOP")), state_dir=self.d)
        with mock.patch("tradebot.live.fetch_candles", return_value=trending_candles()):
            t.preflight()
            t.step()
        self.assertTrue(fake.orders)
        self.assertEqual(audit(self.d, max_open=5), [])


if __name__ == "__main__":
    unittest.main()
