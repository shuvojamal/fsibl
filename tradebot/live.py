"""Trade a real Binance account (testnet by default) with the strategy engine.

Same decision logic as the paper trader, but orders go to the exchange. The
risk guard sits between the strategy and the exchange: it caps how much a
single trade can spend, how much can be lost in a day, and refuses to trade
at all once a kill-switch file exists. Live trading needs an explicit flag.
"""
import csv
import json
import os
import time
from dataclasses import asdict
from datetime import datetime, timezone

from tradebot.binance_client import BinanceClient, BinanceError, fill_summary
from tradebot.data import INTERVAL_MS, fetch_candles
from tradebot.engines import EmaEngine


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class RiskGuard:
    """Says yes or no to every order. Keeps a running daily loss total."""

    def __init__(self, max_trade_usdt, max_daily_loss_usdt, kill_file, state):
        self.max_trade = max_trade_usdt
        self.max_daily_loss = max_daily_loss_usdt
        self.kill_file = kill_file
        self.state = state  # shared dict, persisted by the trader
        self.state.setdefault("day", _today())
        self.state.setdefault("day_pnl", 0.0)

    def _roll_day(self):
        if self.state["day"] != _today():
            self.state["day"], self.state["day_pnl"] = _today(), 0.0

    def can_open(self, usdt):
        self._roll_day()
        if os.path.exists(self.kill_file):
            return False, f"kill switch file {self.kill_file} exists"
        if usdt > self.max_trade:
            return False, f"trade {usdt:.2f} USDT exceeds max {self.max_trade:.2f}"
        if self.state["day_pnl"] <= -self.max_daily_loss:
            return False, f"daily loss {self.state['day_pnl']:.2f} hit the limit {-self.max_daily_loss:.2f}"
        return True, ""

    def can_close(self):
        # Closing a position reduces risk, so only the kill switch blocks it.
        if os.path.exists(self.kill_file):
            return False, f"kill switch file {self.kill_file} exists"
        return True, ""

    def record(self, pnl):
        self._roll_day()
        self.state["day_pnl"] += pnl


class LiveTrader:
    def __init__(self, client: BinanceClient, symbols, interval, params, trade_usdt,
                 guard_args, state_dir, dry_run=False, engine=None):
        self.client, self.interval = client, interval
        self.engine = engine or EmaEngine(params)
        self.symbols = [s.upper() for s in symbols]
        self.trade_usdt, self.dry_run = trade_usdt, dry_run
        os.makedirs(state_dir, exist_ok=True)
        self.state_path = os.path.join(state_dir, "live_state.json")
        self.trades_path = os.path.join(state_dir, "live_trades.csv")
        self.state = self._load()
        self.guard = RiskGuard(*guard_args, state=self.state.setdefault("risk", {}))
        self.state.setdefault("params", asdict(params))
        for s in self.symbols:
            self.state.setdefault("positions", {}).setdefault(
                s, {"qty": 0.0, "entry": 0.0, "stop": 0.0, "target": 0.0, "last_candle": 0})

    def _load(self):
        if os.path.exists(self.state_path):
            with open(self.state_path) as f:
                return json.load(f)
        return {}

    def _save(self):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.state, f, indent=2)
        os.replace(tmp, self.state_path)

    # -- startup checks ---------------------------------------------------

    def preflight(self):
        """Verify keys, balances and symbol filters before the loop starts."""
        offset = self.client.sync_time()
        bal = self.client.balances()
        usdt = bal.get("USDT", 0.0)
        print(f"[{_now()}] connected to {self.client.base_url} (clock offset {offset} ms)")
        print(f"[{_now()}] free USDT: {usdt:,.2f}; per-trade size: {self.trade_usdt:,.2f}")
        if usdt < self.trade_usdt:
            print(f"[{_now()}] WARNING: not enough USDT for one trade")
        for sym in self.symbols:
            f = self.client.symbol_filters(sym)
            if self.trade_usdt < f["min_notional"]:
                raise SystemExit(f"{sym}: per-trade size {self.trade_usdt} is below the exchange "
                                 f"minimum {f['min_notional']}")
            self._reconcile(sym, bal)
        self._save()

    def _reconcile(self, sym, balances):
        """If the exchange holds coins our state doesn't know about, adopt them."""
        pos = self.state["positions"][sym]
        base = sym[:-4] if sym.endswith("USDT") else sym
        held = balances.get(base, 0.0)
        f = self.client.symbol_filters(sym)
        if pos["qty"] == 0 and held >= f["min_qty"]:
            price = self.client.price(sym)
            if held * price >= f["min_notional"]:
                print(f"[{_now()}] {sym}: found {held} {base} on the exchange, treating it as an "
                      f"open position at {price:.4f}")
                pos["qty"], pos["entry"] = held, price
                # No plan was recorded for it, so protect it with a wide safety stop.
                pos["stop"], pos["target"] = price * 0.9, price * 1.2
        elif pos["qty"] > 0 and held < pos["qty"] * 0.99:
            print(f"[{_now()}] {sym}: state says {pos['qty']} but exchange has {held}; "
                  f"trusting the exchange")
            pos["qty"] = held
            if held < f["min_qty"]:
                pos["qty"], pos["entry"] = 0.0, 0.0

    # -- main loop --------------------------------------------------------

    def step(self):
        for sym in self.symbols:
            try:
                self._step_symbol(sym)
            except (OSError, BinanceError) as e:
                print(f"[{_now()}] {sym}: {type(e).__name__}: {e}")
        self._save()

    def _step_symbol(self, sym):
        pos = self.state["positions"][sym]
        candles = fetch_candles(sym, self.interval, self.engine.history)
        last = candles[-1]
        if last.open_time == pos["last_candle"]:
            return
        pos["last_candle"] = last.open_time

        if pos["qty"] > 0:
            if last.low <= pos["stop"]:
                return self._close(sym, pos, "stop_loss")
            if last.high >= pos["target"]:
                return self._close(sym, pos, "take_profit")

        action = self.engine.decide(candles, pos["qty"] > 0)
        if action and action[0] == "buy":
            self._open(sym, pos, action[1], last.close)
        elif action and action[0] == "sell":
            self._close(sym, pos, action[1])

    def _spend(self, plan, price):
        """USDT to spend: the per-trade size, reduced by risk-based sizing if the engine has it."""
        spend = self.trade_usdt
        if hasattr(self.engine, "size"):
            spend = min(spend, self.engine.size(self.trade_usdt, price, plan.stop) * price)
        return spend

    def _open(self, sym, pos, plan, price):
        spend = self._spend(plan, price)
        if spend < self.client.symbol_filters(sym)["min_notional"]:
            print(f"[{_now()}] {sym}: risk-sized order {spend:.2f} USDT is below the exchange minimum")
            return
        ok, why = self.guard.can_open(spend)
        if not ok:
            print(f"[{_now()}] {sym}: BUY blocked: {why}")
            return
        why_buy = "+".join(plan.reasons) or "signal"
        if self.dry_run:
            print(f"[{_now()}] DRY RUN would BUY {spend:.2f} USDT of {sym} at ~{price:.4f} "
                  f"stop {plan.stop:.4f} target {plan.target:.4f} ({why_buy})")
            return
        order = self.client.market_order(sym, "BUY", quote_qty=spend)
        qty, avg, fee = fill_summary(order)
        if qty == 0:
            print(f"[{_now()}] {sym}: BUY not filled ({order.get('status')})")
            return
        pos["qty"], pos["entry"] = qty, avg
        pos["stop"], pos["target"] = plan.stop, plan.target
        self._log(sym, "BUY", qty, avg, fee, why_buy, None, order.get("orderId"))

    def _close(self, sym, pos, reason):
        ok, why = self.guard.can_close()
        if not ok:
            print(f"[{_now()}] {sym}: SELL blocked: {why}")
            return
        if self.dry_run:
            price = self.client.price(sym)
            print(f"[{_now()}] DRY RUN would SELL {pos['qty']} {sym} at ~{price:.4f} ({reason})")
            pos["qty"], pos["entry"], pos["stop"], pos["target"] = 0.0, 0.0, 0.0, 0.0
            return
        order = self.client.market_order(sym, "SELL", qty=pos["qty"])
        qty, avg, fee = fill_summary(order)
        if qty == 0:
            print(f"[{_now()}] {sym}: SELL not filled ({order.get('status')})")
            return
        pnl = qty * (avg - pos["entry"]) - fee
        self.guard.record(pnl)
        self._log(sym, "SELL", qty, avg, fee, reason, pnl, order.get("orderId"))
        pos["qty"], pos["entry"], pos["stop"], pos["target"] = 0.0, 0.0, 0.0, 0.0

    def _log(self, sym, side, qty, price, fee, reason, pnl, order_id):
        pnl_s = "" if pnl is None else f"{pnl:+.4f}"
        print(f"[{_now()}] {side} {sym} {qty} @ {price:.4f} fee {fee:.4f} ({reason}) "
              f"{pnl_s} order {order_id}")
        new = not os.path.exists(self.trades_path)
        with open(self.trades_path, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["time", "symbol", "side", "qty", "price", "fee", "reason",
                            "pnl_usdt", "order_id"])
            w.writerow([_now(), sym, side, qty, f"{price:.8f}", f"{fee:.8f}", reason, pnl_s, order_id])

    def run_forever(self, poll_seconds=None):
        poll = poll_seconds or min(60, INTERVAL_MS[self.interval] // 1000)
        mode = "DRY RUN" if self.dry_run else ("LIVE" if "api.binance.com" in self.client.base_url
                                               else "TESTNET")
        print(f"[{mode}] trading {', '.join(self.symbols)} on {self.interval} candles, "
              f"{self.trade_usdt:.2f} USDT per trade. Ctrl+C to stop; create "
              f"{self.guard.kill_file} to block new orders.")
        while True:
            self.step()
            time.sleep(poll)
