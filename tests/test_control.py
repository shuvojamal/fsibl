import json
import os
import tempfile
import unittest

from tradebot.control import live_args, read_controls, real_money_flags


class Controls(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def put(self, name, text):
        with open(os.path.join(self.d, name), "w") as f:
            f.write(text)

    def test_defaults_match_the_previous_hard_coded_run(self):
        a = live_args(read_controls(self.d, 5000))
        self.assertEqual(a, ["--risk", "0.0100", "--capital", "5000.00", "--trade-usdt", "5000.00",
                             "--max-trade-usdt", "5000.00", "--max-daily-loss", "150.00",
                             "--max-drawdown", "0.3500", "--max-open", "5", "--backstop", "0.2000",
                             "--rebuy-wait-days", "7", "--min-score", "5"])

    def test_settings_are_clamped_and_bad_values_ignored(self):
        self.put("settings.json", json.dumps({"risk_pct": 9, "max_open": 0, "capital": "abc", "gold": False}))
        c = read_controls(self.d, 5000)
        self.assertEqual((c["risk_pct"], c["max_open"], c["capital"], c["gold"]), (2.0, 1, 5000.0, False))
        self.assertEqual(len(c["notes"]), 3)
        self.put("settings.json", "{broken")
        self.assertEqual(read_controls(self.d)["risk_pct"], 1.0)

    def test_close_requests_are_validated_before_reaching_the_shell(self):
        self.put("CLOSE", "btcusdt ETHUSDT\n$(rm -rf /) ALL ;echo")
        c = read_controls(self.d)
        self.assertEqual(c["close"], ["ALL", "BTCUSDT", "ETHUSDT"])
        self.assertEqual(len(c["notes"]), 4)
        self.put("PAUSED", ""); self.put("RESET_HALT", "")
        a = live_args(read_controls(self.d))
        self.assertIn("--pause-entries", a); self.assertIn("--reset-halt", a)
        self.assertEqual(a[-4:], ["--close-now", "ALL", "BTCUSDT", "ETHUSDT"])


    def test_real_money_is_off_unless_the_owner_typed_the_confirmation(self):
        self.assertIsNone(real_money_flags(read_controls(self.d)))            # default: off
        self.put("settings.json", json.dumps({"mode": "test"}))
        self.assertEqual(real_money_flags(read_controls(self.d)), ["--live", "--i-accept-the-risk", "--dry-run"])
        self.put("settings.json", json.dumps({"mode": "live", "confirm": "yes"}))
        c = read_controls(self.d)
        self.assertEqual(c["mode"], "off"); self.assertIsNone(real_money_flags(c))
        self.put("settings.json", json.dumps({"mode": "live", "confirm": "I ACCEPT THE RISK"}))
        self.assertEqual(real_money_flags(read_controls(self.d)), ["--live", "--i-accept-the-risk"])
        self.put("settings.json", json.dumps({"mode": "yolo"}))
        self.assertEqual(read_controls(self.d)["mode"], "off")


if __name__ == "__main__":
    unittest.main()
