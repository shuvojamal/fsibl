import os
import tempfile
import unittest

from tests.test_opportunity import uptrend
from tradebot.data import Candle
from tradebot.shadow import compare, replay, shadow_report, unlisted

DAY = 86_400_000


def daily(candles, end_ms):
    """Re-date candles as consecutive days ending at end_ms."""
    n = len(candles)
    return [Candle(end_ms - (n - 1 - i) * DAY, c.open, c.high, c.low, c.close, c.volume, end_ms - (n - 2 - i) * DAY - 1)
            for i, c in enumerate(candles)]


class Shadow(unittest.TestCase):
    def test_compare_matches_by_coin_side_and_date(self):
        live = [{"time": "2026-10-22 19:26:39 UTC", "symbol": "BTCUSDT", "side": "BUY", "price": "100"},
                {"time": "2026-10-22 19:26:40 UTC", "symbol": "PEPEUSDT", "side": "BUY", "price": "1"}]
        shadow = [{"day": "2026-10-22", "symbol": "BTCUSDT", "side": "BUY", "price": 99.0},
                  {"day": "2026-10-25", "symbol": "ETHUSDT", "side": "BUY", "price": 10.0}]
        both, only_live, only_shadow = compare(live, shadow)
        self.assertEqual([b[0]["symbol"] for b in both], ["BTCUSDT"])
        self.assertEqual([x["symbol"] for x in only_live], ["PEPEUSDT"])
        self.assertEqual([x["symbol"] for x in only_shadow], ["ETHUSDT"])

    def test_replay_buys_an_uptrend_once_at_the_next_open(self):
        cs = daily(uptrend(400), 1_790_000_000_000 // DAY * DAY)
        trades = replay({"BTCUSDT": cs}, cs[-60].open_time)
        buys = [t for t in trades if t["side"] == "BUY"]
        self.assertTrue(buys)
        self.assertTrue(all(t["symbol"] == "BTCUSDT" for t in trades))

    def test_report_skips_unlisted_coins_and_says_when_live_matches(self):
        d = tempfile.mkdtemp()
        cs = daily(uptrend(400), 1_790_000_000_000 // DAY * DAY)
        first = replay({"BTCUSDT": cs}, cs[-60].open_time)[0]
        t = first["day"] + " 00:07:00 UTC"
        with open(os.path.join(d, "live_trades.csv"), "w") as f:
            f.write("time,symbol,side,qty,price,fee,reason,pnl_usdt,order_id\n"
                    f"{t},BTCUSDT,BUY,1,{first['price']:.4f},0.1,trend_up,,1\n")
        with open(os.path.join(d, "run.log"), "w") as f:
            f.write("[2026-10-22 19:26:36 UTC] ZECUSDT: skipped, not tradable on this exchange (x)\n")
        self.assertEqual(unlisted(d), {"ZECUSDT"})
        fetched = []
        def fetch(sym, interval, n):
            fetched.append(sym)
            return cs
        out = "\n".join(shadow_report(d, ["BTCUSDT", "ZECUSDT"], fetch=fetch))
        self.assertNotIn("ZECUSDT", fetched)
        self.assertIn("1 trades matched", out)


if __name__ == "__main__":
    unittest.main()
