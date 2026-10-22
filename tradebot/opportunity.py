"""Opportunity scoring: trade only when several independent checks line up.

Each check is a classic technical-analysis condition. They are scored one
point each, and a trade is only taken when the total reaches `min_score`.
Stops and targets come from ATR (volatility), not fixed percentages, so a
quiet market gets a tight stop and a wild one a wide stop. Position size is
fixed-fractional: a set fraction of equity is risked per trade, so the bot
buys fewer coins when the stop is far away.
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
    stop_atr: float = 2.0      # stop = entry - stop_atr * ATR
    reward_risk: float = 3.0   # target = entry + reward_risk * (entry - stop); 3:1 held up
                               # best across 10 coins in docs/research-round1-2026-10-22.md
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


class Opportunity:
    """Strategy object: prepare(candles) once, then signal(i) / should_exit(i)."""

    CHECKS = 8

    def __init__(self, p=OppParams()):
        self.p = p

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
        target = price + self.p.reward_risk * (price - stop)
        return Plan(stop, target, score, [n for n, ok in checks if ok])

    def should_exit(self, i):
        """Trend has turned: fast EMA below slow EMA."""
        return (self.fast[i] is not None and self.slow[i] is not None
                and self.fast[i] < self.slow[i])

    def size(self, equity, price, stop):
        """Coins to buy so that hitting the stop loses risk_frac of equity."""
        risk_per_coin = price - stop
        if risk_per_coin <= 0:
            return 0.0
        qty = equity * self.p.risk_frac / risk_per_coin
        return min(qty, equity / price)  # never more than we can pay for
