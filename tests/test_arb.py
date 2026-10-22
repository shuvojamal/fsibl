import unittest

from tradebot.arb import best_gap
from tradebot.exchanges import Quote


def q(ex, bid, ask, qty=1.0):
    return Quote(ex, "BTCUSDT", bid, qty, ask, qty)


class BestGapTests(unittest.TestCase):
    def test_picks_cheapest_ask_and_dearest_bid(self):
        g = best_gap([q("binance", 100, 101), q("okx", 103, 104), q("mexc", 99, 100)])
        self.assertEqual((g["buy"].exchange, g["sell"].exchange), ("mexc", "okx"))
        self.assertAlmostEqual(g["gross"], 0.03)
        self.assertAlmostEqual(g["net"], 0.03 - 0.0005 - 0.001)

    def test_same_exchange_never_paired(self):
        g = best_gap([q("binance", 100, 99)])  # crossed book on one venue
        self.assertIsNone(g)

    def test_quantity_is_smaller_side(self):
        g = best_gap([q("binance", 100, 101, qty=5), q("okx", 103, 104, qty=0.2)])
        self.assertEqual(g["qty"], 0.2)

    def test_tiny_gap_is_negative_after_fees(self):
        g = best_gap([q("binance", 100.00, 100.01), q("okx", 100.02, 100.03)])
        self.assertLess(g["net"], 0)


if __name__ == "__main__":
    unittest.main()
