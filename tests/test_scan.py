import unittest
from unittest import mock

from tests.test_opportunity import candles, uptrend
from tradebot.scan import format_scan, scan


def fake_fetch(sym, interval, count):
    if sym == "BADUSDT":
        raise OSError("no such symbol")
    if sym == "BIGUSDT":
        return candles([c.close for c in uptrend()], vol=1000.0)  # most traded
    return uptrend()


class ScanTests(unittest.TestCase):
    def test_ranks_by_volume_keeps_top_n_and_skips_bad_symbols(self):
        with mock.patch("tradebot.scan.fetch_candles", side_effect=fake_fetch):
            rows, skipped = scan(["SMALL", "BIG", "BAD"], top=1)
        self.assertEqual([r[0] for r in rows], ["BIGUSDT"])
        self.assertEqual(skipped, ["BADUSDT"])

    def test_format_marks_signals(self):
        with mock.patch("tradebot.scan.fetch_candles", side_effect=fake_fetch):
            rows, _ = scan(["BIG"], top=5)
        text = "\n".join(format_scan(rows))
        self.assertIn("BIGUSDT", text)
        self.assertRegex(text, r"\d/8")


if __name__ == "__main__":
    unittest.main()
