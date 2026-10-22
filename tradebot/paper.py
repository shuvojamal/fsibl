"""Paper trading: run the strategy on live Binance prices with fake money.

Each symbol gets an equal slice of the starting capital. State is saved to
disk after every check, so the bot can be stopped and restarted.
"""
import csv
import json
import os
import time
from dataclasses import asdict
from datetime import datetime, timezone

from tradebot.backtest import FEE, SLIPPAGE
from tradebot.data import INTERVAL_MS, fetch_candles
from tradebot.strategy import BUY, SELL, Params, compute, decide

HISTORY = 300  # candles needed to warm up the indicators


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


class PaperTrader:
    def __init__(self, symbols, interval, params, capital, state_dir="paper_state"):
        self.symbols = [s.upper() for s in symbols]
        self.interval, self.p = interval, params
        self.state_path = os.path.join(state_dir, "state.json")
        self.trades_path = os.path.join(state_dir, "trades.csv")
        os.makedirs(state_dir, exist_ok=True)
        if os.path.exists(self.state_path):
            with open(self.state_path) as f:
                self.state = json.load(f)
            for s in self.symbols:  # symbols added since last run start flat
                self.state["positions"].setdefault(s, self._flat(capital / len(self.symbols)))
        else:
            share = capital / len(self.symbols)
            self.state = {"params": asdict(params),
                          "positions": {s: self._flat(share) for s in self.symbols}}

    @staticmethod
    def _flat(cash):
        return {"cash": cash, "qty": 0.0, "entry": 0.0, "last_candle": 0}

    def step(self):
        """Check every symbol once. Returns total equity in USDT."""
        total = 0.0
        for sym in self.symbols:
            try:
                total += self._step_symbol(sym)
            except OSError as e:
                print(f"[{_now()}] {sym}: network error, skipping ({e})")
                pos = self.state["positions"][sym]
                total += pos["cash"] + pos["qty"] * pos["entry"]
        self._save()
        return total

    def _step_symbol(self, sym):
        pos = self.state["positions"][sym]
        candles = fetch_candles(sym, self.interval, HISTORY)
        last = candles[-1]
        price = last.close

        if last.open_time != pos["last_candle"]:  # act once per new closed candle
            pos["last_candle"] = last.open_time
            if pos["qty"] > 0:
                stop = pos["entry"] * (1 - self.p.stop_loss)
                target = pos["entry"] * (1 + self.p.take_profit)
                if last.low <= stop:
                    self._sell(sym, pos, min(stop, price), "stop_loss")
                elif last.high >= target:
                    self._sell(sym, pos, max(target, price), "take_profit")
            ind = compute([c.close for c in candles], self.p)
            action = decide(len(candles) - 1, ind, self.p, pos["qty"] > 0)
            if action == BUY:
                self._buy(sym, pos, price)
            elif action == SELL:
                self._sell(sym, pos, price, "signal")
        return pos["cash"] + pos["qty"] * price

    def _buy(self, sym, pos, price):
        fill = price * (1 + SLIPPAGE)
        pos["qty"] = pos["cash"] * (1 - FEE) / fill
        pos["entry"], pos["cash"] = fill, 0.0
        self._log(sym, "BUY", fill, pos["qty"], "signal", None)

    def _sell(self, sym, pos, price, reason):
        fill = price * (1 - SLIPPAGE)
        qty = pos["qty"]
        pos["cash"] = qty * fill * (1 - FEE)
        ret = fill / pos["entry"] * (1 - FEE) ** 2 - 1
        pos["qty"], pos["entry"] = 0.0, 0.0
        self._log(sym, "SELL", fill, qty, reason, ret)

    def _log(self, sym, side, price, qty, reason, ret):
        pnl = "" if ret is None else f"{ret:+.2%}"
        print(f"[{_now()}] {side} {sym} qty={qty:.6f} @ {price:.4f} ({reason}) {pnl}")
        new = not os.path.exists(self.trades_path)
        with open(self.trades_path, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["time", "symbol", "side", "price", "qty", "reason", "return"])
            w.writerow([_now(), sym, side, f"{price:.8f}", f"{qty:.8f}", reason, pnl])

    def _save(self):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.state, f, indent=2)
        os.replace(tmp, self.state_path)

    def run_forever(self, poll_seconds=None):
        poll = poll_seconds or min(60, INTERVAL_MS[self.interval] // 1000)
        print(f"Paper trading {', '.join(self.symbols)} on {self.interval} candles. Ctrl+C to stop.")
        while True:
            equity = self.step()
            print(f"[{_now()}] equity: {equity:,.2f} USDT")
            time.sleep(poll)
