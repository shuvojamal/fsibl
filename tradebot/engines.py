"""Decision engines shared by the paper and live traders.

An engine looks at the closed candles for one symbol and says what to do:
    ("buy", Plan)      open a position with this stop and target
    ("sell", reason)   close the position
    None               nothing
Stops and targets are stored on the position so the trader can check them
against each new candle's high and low.
"""
from tradebot.opportunity import Opportunity, OppParams, Plan
from tradebot.strategy import BUY, SELL, Params, compute, decide


class EmaEngine:
    """EMA crossover + RSI filter, fixed-percentage stop and target."""
    name = "ema"

    def __init__(self, p: Params):
        self.p = p
        self.history = 300

    def decide(self, candles, in_position):
        ind = compute([c.close for c in candles], self.p)
        action = decide(len(candles) - 1, ind, self.p, in_position)
        if action == BUY:
            price = candles[-1].close
            return ("buy", Plan(price * (1 - self.p.stop_loss),
                                price * (1 + self.p.take_profit), 0, ["ema_cross"]))
        if action == SELL:
            return ("sell", "signal")
        return None


class OpportunityEngine:
    """Multi-check scorer with ATR stops; trades only when enough checks agree."""
    name = "opportunity"

    def __init__(self, p: OppParams):
        self.p = p
        self.strat = Opportunity(p)
        self.history = p.warmup + 100

    def decide(self, candles, in_position):
        s = self.strat.prepare(candles)
        i = len(candles) - 1
        if in_position:
            return ("sell", "signal") if s.should_exit(i) else None
        plan = s.signal(i)
        return ("buy", plan) if plan else None

    def size(self, equity, price, stop):
        return self.strat.size(equity, price, stop)

    def trail_stop(self, candles, pos):
        """New stop for an open position after the latest closed candle (never lower)."""
        s = self.strat.prepare(candles)
        s.peak = max(pos.get("peak") or pos["entry"], candles[-1].close)
        pos["peak"] = s.peak
        return s.update_stop(len(candles) - 1, pos["stop"])


def make_engine(name, ema_params=None, opp_params=None):
    if name == "opportunity":
        return OpportunityEngine(opp_params or OppParams())
    return EmaEngine(ema_params or Params())
