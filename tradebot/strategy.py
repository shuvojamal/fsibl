"""Trend-following strategy: EMA crossover with an RSI filter.

Long-only (spot). Decisions are made on a closed candle and executed at the
next candle's open, so the backtest never peeks at the future. Stop-loss and
take-profit are checked by the executor against each candle's high/low.
"""
from dataclasses import dataclass

from tradebot.indicators import ema, rsi

BUY, SELL, HOLD = "buy", "sell", "hold"


@dataclass(frozen=True)
class Params:
    fast: int = 12
    slow: int = 26
    rsi_period: int = 14
    rsi_max: float = 70.0      # skip entries when RSI is above this (overbought)
    stop_loss: float = 0.03    # exit if price falls 3% below entry
    take_profit: float = 0.06  # exit if price rises 6% above entry


@dataclass
class Indicators:
    fast: list
    slow: list
    rsi: list


def compute(closes, p):
    return Indicators(ema(closes, p.fast), ema(closes, p.slow), rsi(closes, p.rsi_period))


def decide(i, ind, p, in_position):
    """Action to take after candle `i` closes."""
    if i < 1 or None in (ind.fast[i], ind.slow[i], ind.rsi[i], ind.fast[i - 1], ind.slow[i - 1]):
        return HOLD
    trend_up = ind.fast[i] > ind.slow[i]
    if in_position:
        return SELL if not trend_up else HOLD
    crossed_up = trend_up and ind.fast[i - 1] <= ind.slow[i - 1]
    return BUY if crossed_up and ind.rsi[i] < p.rsi_max else HOLD
