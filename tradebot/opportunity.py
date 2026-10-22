"""Opportunity scoring: trade only when several independent checks line up.

Each check is a classic technical-analysis condition. They are scored one
point each, and a trade is only taken when the total reaches `min_score`.
Stops come from ATR (volatility), not fixed percentages, so a quiet market
gets a tight stop and a wild one a wide stop. Position size is
fixed-fractional: a set fraction of equity is risked per trade, so the bot
buys fewer coins when the stop is far away.

Exit: by default a trailing ("chandelier") stop that follows the highest
close since entry minus `trail_atr` ATRs, which lets a real trend pay far
more than a fixed target. With `trail_atr=0` the older exit applies: a
fixed `reward_risk` target plus the fast/slow EMA turning down.
"""
from dataclasses import dataclass, field

from tradebot.indicators import atr, ema, macd, rolling_max, rsi, sma


@dataclass(frozen=True)
class OppParams:
    fast: int = 20
    slow: int = 50
    trend: int = 200           # long-term EMA
    rsi_lo: float = 45.0
    rsi_hi: float = 65.0
    vol_period: int = 20
    atr_period: int = 14
    atr_min: float = 0.005     # ATR as a fraction of price: too quiet below this
    atr_max: float = 0.05      # ...and too wild above this
    breakout: int = 20
    stop_atr: float = 2.0      # initial stop = entry - stop_atr * ATR
    trail_atr: float = 3.0     # trailing stop = highest close - trail_atr * ATR; 0 = off
    reward_risk: float = 3.0   # only with trail_atr=0: target = entry + reward_risk * risk
    risk_frac: float = 0.01    # fraction of equity risked per trade
    min_score: int = 5         # out of 8

    @property
    def warmup(self):
        return self.trend + 2


@dataclass
class Plan:
    """A proposed trade: where to get out if wrong, where to take profit."""
    stop: float
    target: float
    score: int
    reasons: list = field(default_factory=list)


NO_TARGET = 1000.0  # multiplier: a target this far away never fills


class Opportunity:
    """Strategy object: prepare(candles) once, then signal(i) / update_stop(i) / should_exit(i)."""

    CHECKS = 8

    def __init__(self, p=OppParams()):
        self.p = p
        self.peak = None  # highest close since entry, for the trailing stop

    def prepare(self, candles):
        p = self.p
        self.closes = c = [x.close for x in candles]
        highs, lows = [x.high for x in candles], [x.low for x in candles]
        vols = [x.volume for x in candles]
        self.fast, self.slow, self.trend = ema(c, p.fast), ema(c, p.slow), ema(c, p.trend)
        self.rsi = rsi(c, 14)
        _, _, self.hist = macd(c)
        self.vol_avg = sma(vols, p.vol_period)
        self.vols = vols
        self.atr = atr(highs, lows, c, p.atr_period)
        self.high_n = rolling_max(highs, p.breakout)
        return self

    def checks(self, i):
        """List of (name, passed) for candle i, or None if indicators aren't ready."""
        p = self.p
        needed = (self.fast[i], self.slow[i], self.trend[i], self.rsi[i], self.hist[i],
                  self.vol_avg[i], self.atr[i], self.high_n[i])
        if i < 2 or any(v is None for v in needed) or self.trend[i - 2] is None \
                or self.hist[i - 1] is None or self.high_n[i - 1] is None:
            return None
        price, a = self.closes[i], self.atr[i]
        return [
            ("trend_up", price > self.trend[i] and self.trend[i] > self.trend[i - 2]),
            ("ema_aligned", self.fast[i] > self.slow[i]),
            ("momentum", self.hist[i] > 0 and self.hist[i] > self.hist[i - 1]),
            ("rsi_zone", p.rsi_lo <= self.rsi[i] <= p.rsi_hi),
            ("volume", self.vols[i] > self.vol_avg[i]),
            ("volatility_ok", p.atr_min <= a / price <= p.atr_max),
            ("breakout", price > self.high_n[i - 1]),
            ("pullback", abs(price - self.fast[i]) <= a),
        ]

    def signal(self, i):
        """A Plan if candle i is an opportunity, else None."""
        checks = self.checks(i)
        if checks is None:
            return None
        score = sum(ok for _, ok in checks)
        if score < self.p.min_score:
            return None
        price, a = self.closes[i], self.atr[i]
        stop = price - self.p.stop_atr * a
        if stop <= 0:
            return None
        if self.p.trail_atr > 0:
            self.peak = price
            target = price * NO_TARGET
        else:
            target = price + self.p.reward_risk * (price - stop)
        return Plan(stop, target, score, [n for n, ok in checks if ok])

    def update_stop(self, i, stop):
        """Trailing stop after candle i closes; never lower than the current stop."""
        if self.p.trail_atr <= 0 or self.atr[i] is None:
            return stop
        self.peak = max(self.peak or 0.0, self.closes[i])
        return max(stop, self.peak - self.p.trail_atr * self.atr[i])

    def should_exit(self, i):
        """Without a trail: the trend has turned (fast EMA below slow EMA)."""
        if self.p.trail_atr > 0:
            return False
        return (self.fast[i] is not None and self.slow[i] is not None
                and self.fast[i] < self.slow[i])

    def size(self, equity, price, stop):
        """Coins to buy so that hitting the stop loses risk_frac of equity."""
        risk_per_coin = price - stop
        if risk_per_coin <= 0:
            return 0.0
        qty = equity * self.p.risk_frac / risk_per_coin
        return min(qty, equity / price)  # never more than we can pay for
