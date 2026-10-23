import unittest

from tradebot.funding import format_funding, scan_funding, trailing_funding

DAY = 86_400_000


def fake(rates):
    """OKX-shaped history: one payment every 8 hours, newest first."""
    def get(url):
        coin = url.split("instId=")[1].split("-")[0]
        if coin not in rates:
            return {"code": "51001", "data": []}
        now = 100 * DAY
        return {"data": [{"fundingTime": str(now - i * DAY // 3), "fundingRate": str(rates[coin]), "realizedRate": str(rates[coin])}
                         for i in range(60)]}
    return get


class Funding(unittest.TestCase):
    def test_annualises_last_seven_days_only(self):
        # 0.01% per 8h = 0.03% a day = 10.95% a year; older payments beyond 7 days are ignored
        self.assertAlmostEqual(trailing_funding("BTC", fake({"BTC": 0.0001})), 0.0003 * 365, places=6)

    def test_flags_only_high_funding_and_handles_missing(self):
        rows = scan_funding(["BTCUSDT", "ETH", "XYZ"], fake({"BTC": 0.0001, "ETH": 0.0003}))
        self.assertEqual([r[0] for r in rows], ["ETH", "BTC", "XYZ"])
        text = "\n".join(format_funding(rows))
        self.assertIn("ETH", text.split("CARRY OPPORTUNITY")[0])
        self.assertEqual(text.count("CARRY OPPORTUNITY"), 1)
        self.assertIn("no perpetual", text)

    def test_says_so_when_nothing_qualifies(self):
        self.assertIn("no carry opportunity", "\n".join(format_funding(scan_funding(["BTC"], fake({"BTC": 0.00001})))))


if __name__ == "__main__":
    unittest.main()
