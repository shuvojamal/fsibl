import unittest

from tradebot import backtest
from tradebot.data import Candle
from tradebot.indicators import ema, rsi
from tradebot.strategy import BUY, HOLD, SELL, Indicators, Params, decide


def candles_from(closes, spread=0.001):
    out, prev = [], closes[0]
    for i, c in enumerate(closes):
        hi, lo = max(prev, c) * (1 + spread), min(prev, c) * (1 - spread)
        out.append(Candle(i * 3600_000, prev, hi, lo, c, 1.0, (i + 1) * 3600_000 - 1))
        prev = c
    return out


class IndicatorTests(unittest.TestCase):
    def test_ema_of_constant_is_constant(self):
        self.assertAlmostEqual(ema([5.0] * 30, 10)[-1], 5.0)

    def test_rsi_extremes(self):
        self.assertEqual(rsi(list(range(1, 40)), 14)[-1], 100.0)
        self.assertLess(rsi(list(range(40, 1, -1)), 14)[-1], 1.0)


class StrategyTests(unittest.TestCase):
    def test_crossover_buys_and_crossunder_sells(self):
        p = Params()
        up = Indicators(fast=[1, 3], slow=[2, 2], rsi=[50, 50])
        self.assertEqual(decide(1, up, p, in_position=False), BUY)
        down = Indicators(fast=[3, 1], slow=[2, 2], rsi=[50, 50])
        self.assertEqual(decide(1, down, p, in_position=True), SELL)

    def test_overbought_blocks_entry(self):
        ind = Indicators(fast=[1, 3], slow=[2, 2], rsi=[50, 90])
        self.assertEqual(decide(1, ind, Params(rsi_max=70), in_position=False), HOLD)


class BacktestTests(unittest.TestCase):
    def test_flat_market_loses_only_to_costs(self):
        res = backtest.run(candles_from([100.0] * 200))
        self.assertEqual(res.trades, [])
        self.assertAlmostEqual(res.total_return, 0.0)

    def test_fees_make_round_trip_negative(self):
        t = backtest.Trade(0, 100.0, 1, 100.0, "signal")
        self.assertLess(t.ret, 0)

    def test_stop_loss_triggers_in_crash(self):
        closes = [100 - i * 0.5 for i in range(60)] + [80 + i for i in range(30)] + [60] * 10
        res = backtest.run(candles_from(closes), Params(fast=3, slow=10, rsi_max=101, take_profit=10))
        self.assertTrue(any(t.reason == "stop_loss" for t in res.trades))
        self.assertGreater(res.final_equity, 0)

    def test_no_lookahead_entry_fills_next_open(self):
        closes = [100 - i * 0.5 for i in range(60)] + [80 + i for i in range(30)]
        cs = candles_from(closes)
        res = backtest.run(cs, Params(fast=3, slow=10, rsi_max=101, take_profit=10))
        first = res.trades[0]
        idx = first.entry_time // 3600_000
        self.assertAlmostEqual(first.entry_price, cs[idx].open * (1 + backtest.SLIPPAGE))


if __name__ == "__main__":
    unittest.main()
