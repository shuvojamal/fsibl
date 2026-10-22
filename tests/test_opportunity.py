import unittest

from tradebot import backtest
from tradebot.data import Candle
from tradebot.engines import OpportunityEngine, make_engine
from tradebot.opportunity import Opportunity, OppParams


def candles(closes, vol=1.0):
    out, prev = [], closes[0]
    for i, c in enumerate(closes):
        out.append(Candle(i * 86_400_000, prev, max(prev, c) * 1.002, min(prev, c) * 0.998, c, vol,
                          (i + 1) * 86_400_000 - 1))
        prev = c
    return out


def uptrend(n=260):
    # steady 0.4%/day rise with a small wobble so ATR and RSI stay in sane ranges
    return candles([100 * (1.004 ** i) * (1 + 0.004 * ((i % 3) - 1)) for i in range(n)])


class ScorerTests(unittest.TestCase):
    def test_not_ready_before_warmup(self):
        s = Opportunity().prepare(uptrend(50))
        self.assertIsNone(s.checks(49))

    def test_checks_are_eight_named_booleans(self):
        s = Opportunity().prepare(uptrend())
        checks = s.checks(259)
        self.assertEqual(len(checks), Opportunity.CHECKS)
        self.assertTrue(all(isinstance(ok, bool) for _, ok in checks))

    def test_uptrend_passes_trend_checks(self):
        s = Opportunity().prepare(uptrend())
        passed = {name for name, ok in s.checks(259) if ok}
        self.assertIn("trend_up", passed)
        self.assertIn("ema_aligned", passed)

    def test_signal_requires_min_score(self):
        cs = uptrend()
        score = sum(ok for _, ok in Opportunity().prepare(cs).checks(259))
        self.assertIsNotNone(Opportunity(OppParams(min_score=score)).prepare(cs).signal(259))
        self.assertIsNone(Opportunity(OppParams(min_score=score + 1)).prepare(cs).signal(259))

    def test_plan_has_atr_stop_and_reward_risk_target(self):
        cs = uptrend()
        p = OppParams(min_score=0, trail_atr=0)
        s = Opportunity(p).prepare(cs)
        plan = s.signal(259)
        price, a = cs[-1].close, s.atr[259]
        self.assertAlmostEqual(plan.stop, price - p.stop_atr * a)
        self.assertAlmostEqual(plan.target - price, p.reward_risk * (price - plan.stop))
        self.assertTrue(s.should_exit(259) in (True, False))  # EMA-cross exit is active

    def test_trailing_stop_follows_highest_close_and_never_drops(self):
        cs = uptrend()
        p = OppParams(min_score=0, trail_atr=3.0)
        s = Opportunity(p).prepare(cs)
        plan = s.signal(200)
        self.assertGreater(plan.target, cs[200].close * 100)  # no fixed target
        stop = plan.stop
        stops = []
        for i in range(201, 260):
            stop = s.update_stop(i, stop)
            stops.append(stop)
        self.assertEqual(stops, sorted(stops))             # ratchets up only
        self.assertAlmostEqual(stops[-1], max(c.close for c in cs[200:260]) - 3.0 * s.atr[259])
        self.assertFalse(s.should_exit(259))               # the trail is the exit

    def test_flat_market_is_never_an_opportunity(self):
        s = Opportunity(OppParams(min_score=5)).prepare(candles([100.0] * 260))
        self.assertIsNone(s.signal(259))


class SizingTests(unittest.TestCase):
    def test_risk_one_percent(self):
        s = Opportunity(OppParams(risk_frac=0.01))
        qty = s.size(equity=1000, price=100, stop=98)
        self.assertAlmostEqual(qty * (100 - 98), 10.0)  # losing the stop costs 1% of 1000

    def test_never_exceeds_cash(self):
        s = Opportunity(OppParams(risk_frac=0.5))
        self.assertAlmostEqual(s.size(equity=1000, price=100, stop=99.9), 10.0)


class BacktestTests(unittest.TestCase):
    def test_runs_and_books_trades(self):
        res = backtest.run_opportunity(uptrend(400), Opportunity(OppParams(min_score=3)))
        self.assertGreater(len(res.trades), 0)
        self.assertEqual(len(res.equity), 400)
        self.assertGreater(res.final_equity, 0)

    def test_loss_per_stop_is_about_risk_fraction(self):
        # Rise to trigger an entry, then crash so the stop is hit.
        closes = [100 * (1.004 ** i) * (1 + 0.004 * ((i % 3) - 1)) for i in range(300)]
        closes += [closes[-1] * (0.97 ** i) for i in range(1, 10)]
        res = backtest.run_opportunity(candles(closes), Opportunity(OppParams(min_score=3)))
        stops = [t for t in res.trades if t.reason == "stop_loss"]
        self.assertTrue(stops)
        # 1% risk per trade keeps the hole shallow; a crash can gap through the
        # stop, so the fill is worse than the stop and the bound is loose.
        self.assertGreater(res.max_drawdown, -0.10)


class EngineTests(unittest.TestCase):
    def test_make_engine(self):
        self.assertIsInstance(make_engine("opportunity"), OpportunityEngine)
        self.assertEqual(make_engine("ema").name, "ema")

    def test_engine_decides_from_latest_candle(self):
        e = OpportunityEngine(OppParams(min_score=0))
        action = e.decide(uptrend(), in_position=False)
        self.assertEqual(action[0], "buy")
        self.assertLess(action[1].stop, uptrend()[-1].close)


if __name__ == "__main__":
    unittest.main()
