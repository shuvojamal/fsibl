"""Replay a strategy over historical candles, with fees and slippage."""
import itertools
from dataclasses import dataclass, field

from tradebot.strategy import BUY, SELL, Params, compute, decide

FEE = 0.001       # Binance spot taker fee: 0.1% per side
SLIPPAGE = 0.0005  # assume we fill 0.05% worse than the quoted price


@dataclass
class Trade:
    entry_time: int
    entry_price: float
    exit_time: int
    exit_price: float
    reason: str

    @property
    def ret(self):
        """Net return of the trade after fees on both sides."""
        return (self.exit_price / self.entry_price) * (1 - FEE) ** 2 - 1


@dataclass
class Result:
    trades: list = field(default_factory=list)
    equity: list = field(default_factory=list)
    start_capital: float = 0.0
    buy_hold_return: float = 0.0

    @property
    def final_equity(self):
        return self.equity[-1] if self.equity else self.start_capital

    @property
    def total_return(self):
        return self.final_equity / self.start_capital - 1

    @property
    def win_rate(self):
        return sum(t.ret > 0 for t in self.trades) / len(self.trades) if self.trades else 0.0

    @property
    def profit_factor(self):
        gains = sum(t.ret for t in self.trades if t.ret > 0)
        losses = -sum(t.ret for t in self.trades if t.ret <= 0)
        return gains / losses if losses else float("inf") if gains else 0.0

    @property
    def avg_win(self):
        wins = [t.ret for t in self.trades if t.ret > 0]
        return sum(wins) / len(wins) if wins else 0.0

    @property
    def avg_loss(self):
        losses = [t.ret for t in self.trades if t.ret <= 0]
        return sum(losses) / len(losses) if losses else 0.0

    @property
    def max_drawdown(self):
        peak, worst = float("-inf"), 0.0
        for e in self.equity:
            peak = max(peak, e)
            worst = min(worst, e / peak - 1)
        return worst


def run(candles, p=Params(), capital=1000.0):
    ind = compute([c.close for c in candles], p)
    res = Result(start_capital=capital)
    cash, qty, entry, entry_time = capital, 0.0, 0.0, 0
    pending = None  # action decided on the previous close, filled at this open

    for i, c in enumerate(candles):
        if pending == BUY and qty == 0:
            entry = c.open * (1 + SLIPPAGE)
            qty, cash, entry_time = cash * (1 - FEE) / entry, 0.0, c.open_time
        elif pending == SELL and qty > 0:
            cash, qty = _close(res, qty, entry, entry_time, c.open * (1 - SLIPPAGE),
                               c.open_time, "signal")
        pending = None

        if qty > 0:
            stop, target = entry * (1 - p.stop_loss), entry * (1 + p.take_profit)
            # If both levels sit inside one candle we can't know which came
            # first, so assume the worse one (the stop).
            if c.low <= stop:
                cash, qty = _close(res, qty, entry, entry_time,
                                   min(stop, c.open) * (1 - SLIPPAGE), c.open_time, "stop_loss")
            elif c.high >= target:
                cash, qty = _close(res, qty, entry, entry_time,
                                   max(target, c.open) * (1 - SLIPPAGE), c.open_time, "take_profit")

        action = decide(i, ind, p, qty > 0)
        if action in (BUY, SELL):
            pending = action
        res.equity.append(cash + qty * c.close)

    if qty > 0:  # mark the open position to market at the end
        last = candles[-1]
        cash, qty = _close(res, qty, entry, entry_time, last.close * (1 - SLIPPAGE),
                           last.close_time, "end")
        res.equity[-1] = cash
    if candles:
        res.buy_hold_return = candles[-1].close / candles[0].open * (1 - FEE) ** 2 - 1
    return res


def _close(res, qty, entry, entry_time, price, time, reason, cash=0.0):
    res.trades.append(Trade(entry_time, entry, time, price, reason))
    return cash + qty * price * (1 - FEE), 0.0


GRID = {
    "fast": [5, 9, 12, 20],
    "slow": [26, 50, 100],
    "rsi_max": [60, 70, 80],
    "stop_loss": [0.02, 0.03, 0.05],
    "take_profit": [0.04, 0.06, 0.10],
}


def optimize(candles, train_frac=0.7, min_trades=5):
    """Pick the best parameters on the first part of the data, then report how
    they do on the rest, which they never saw (walk-forward check)."""
    split = int(len(candles) * train_frac)
    train, test = candles[:split], candles[split:]
    best = None
    for combo in itertools.product(*GRID.values()):
        p = Params(**dict(zip(GRID, combo)))
        if p.fast >= p.slow:
            continue
        r = run(train, p)
        if len(r.trades) < min_trades:
            continue
        if best is None or r.total_return > best[1].total_return:
            best = (p, r)
    if best is None:
        return None
    return best[0], best[1], run(test, best[0])


def run_opportunity(candles, strat, capital=1000.0):
    """Replay an Opportunity strategy: per-trade ATR stop/target, risk-sized."""
    strat.prepare(candles)
    res = Result(start_capital=capital)
    cash, qty, entry, entry_time = capital, 0.0, 0.0, 0
    stop = target = 0.0
    pending = None  # (action, plan) decided on the previous close

    for i, c in enumerate(candles):
        if pending and pending[0] == BUY and qty == 0:
            plan = pending[1]
            entry = c.open * (1 + SLIPPAGE)
            qty = min(strat.size(cash, entry, plan.stop), cash * (1 - FEE) / entry)
            if qty > 0:
                cash -= qty * entry / (1 - FEE)
                entry_time, stop, target = c.open_time, plan.stop, plan.target
        elif pending and pending[0] == SELL and qty > 0:
            cash, qty = _close(res, qty, entry, entry_time, c.open * (1 - SLIPPAGE),
                               c.open_time, "signal", cash)
        pending = None

        if qty > 0:
            if c.low <= stop:
                cash, qty = _close(res, qty, entry, entry_time,
                                   min(stop, c.open) * (1 - SLIPPAGE), c.open_time, "stop_loss", cash)
            elif c.high >= target:
                cash, qty = _close(res, qty, entry, entry_time,
                                   max(target, c.open) * (1 - SLIPPAGE), c.open_time, "take_profit", cash)

        if qty > 0:
            # A strategy may ratchet the stop up as the trade works (trailing stop).
            if hasattr(strat, "update_stop"):
                stop = max(stop, strat.update_stop(i, stop))
            if strat.should_exit(i):
                pending = (SELL, None)
        else:
            plan = strat.signal(i)
            if plan:
                pending = (BUY, plan)
        res.equity.append(cash + qty * c.close)

    if qty > 0:
        last = candles[-1]
        cash, qty = _close(res, qty, entry, entry_time, last.close * (1 - SLIPPAGE),
                           last.close_time, "end", cash)
        res.equity[-1] = cash
    if candles:
        res.buy_hold_return = candles[-1].close / candles[0].open * (1 - FEE) ** 2 - 1
    return res
