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
                 guard_args, state_dir, dry_run=False, engine=None, adopt=True, max_open=0,
                 capital=0.0):
        self.client, self.interval = client, interval
        self.engine = engine or EmaEngine(params)
        self.adopt = adopt  # treat coins already on the exchange as the bot's positions?
        self.max_open = max_open  # cap on simultaneous positions; 0 = no cap
        # Trade as if the account held only this much (plus the bot's own P&L),
        # whatever the exchange balance is. 0 = use the whole balance.
        self.capital = capital
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
        for sym in list(self.symbols):
            try:
                f = self.client.symbol_filters(sym)
            except BinanceError as e:
                # Not every coin is listed on every exchange (or on its demo).
                # Skip it rather than refuse to trade the rest.
                held = self.state["positions"].get(sym, {}).get("qty", 0) > 0
                print(f"[{_now()}] {sym}: skipped, not tradable on this exchange ({e.msg})"
                      + (" WARNING: state shows an open position" if held else ""))
                self.symbols.remove(sym)
                continue
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
        if pos["qty"] == 0 and held >= f["min_qty"] and self.adopt:
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
        # Exits first, then buys: when more coins signal than there are free
        # slots, the highest-scoring ones get them (research round 11).
        buys = []
        for sym in self.symbols:
            try:
                buy = self._step_symbol(sym)
                if buy:
                    buys.append(buy)
            except (OSError, BinanceError) as e:
                print(f"[{_now()}] {sym}: {type(e).__name__}: {e}")
        buys.sort(key=lambda b: -b[2].score)
        for sym, pos, plan, price in buys:
            try:
                self._open(sym, pos, plan, price)
            except (OSError, BinanceError) as e:
                print(f"[{_now()}] {sym}: {type(e).__name__}: {e}")
        self._save()

    def _step_symbol(self, sym):
        pos = self.state["positions"][sym]
        candles = fetch_candles(sym, self.interval, self.engine.history)
        last = candles[-1]
        if last.open_time == pos["last_candle"]:
            return None
        pos["last_candle"] = last.open_time

        if pos["qty"] > 0:
            if last.low <= pos["stop"]:
                self._close(sym, pos, "stop_loss")
                return None
            if last.high >= pos["target"]:
                self._close(sym, pos, "take_profit")
                return None
            if hasattr(self.engine, "trail_stop"):
                new_stop = self.engine.trail_stop(candles, pos)
                if new_stop > pos["stop"]:
                    print(f"[{_now()}] {sym}: stop raised {pos['stop']:.4f} -> {new_stop:.4f}")
                    pos["stop"] = new_stop

        action = self.engine.decide(candles, pos["qty"] > 0)
        if action and action[0] == "buy":
            return (sym, pos, action[1], last.close)  # opened by step(), best score first
        if action and action[0] == "sell":
            self._close(sym, pos, action[1])
        return None

    def _equity(self):
        """Account value in USDT for sizing.

        With `capital` set, the bot runs its own virtual sub-account: starting
        capital plus realised P&L plus open positions marked to market. Without
        it, the whole exchange balance counts.
        """
        held = {sym: pos for sym, pos in self.state["positions"].items() if pos["qty"] > 0}
        if self.capital:
            unreal = sum(p["qty"] * (self.client.price(s) - p["entry"]) for s, p in held.items())
            return self.capital + self.state.get("realised", 0.0) + unreal
        total = self.client.balances().get("USDT", 0.0)
        for sym, pos in held.items():
            total += pos["qty"] * self.client.price(sym)
        return total

    def _bot_cash(self):
        """With `capital` set: cash left in the virtual sub-account."""
        invested = sum(p["qty"] * p["entry"] for p in self.state["positions"].values() if p["qty"] > 0)
        return self.capital + self.state.get("realised", 0.0) - invested

    def _spend(self, plan, price):
        """USDT to spend on this buy.

        Engines with risk-based sizing (the opportunity scorer) size the trade
        so that hitting the stop loses `risk_frac` of the whole account; the
        per-trade size then acts only as a cap. Other engines spend the
        per-trade size outright.
        """
        spend = self.trade_usdt
        if hasattr(self.engine, "size"):
            spend = min(spend, self.engine.size(self._equity(), price, plan.stop) * price)
        if self.capital:
            spend = min(spend, max(0.0, self._bot_cash()))
        return spend

    def _open(self, sym, pos, plan, price):
        if self.max_open:
            open_now = sum(1 for p in self.state["positions"].values() if p["qty"] > 0)
            if open_now >= self.max_open:
                print(f"[{_now()}] {sym}: BUY skipped, {open_now} positions open (cap {self.max_open})")
                return
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
        self.state["realised"] = self.state.get("realised", 0.0) + pnl
        self._log(sym, "SELL", qty, avg, fee, reason, pnl, order.get("orderId"))
        pos["qty"], pos["entry"], pos["stop"], pos["target"] = 0.0, 0.0, 0.0, 0.0

    def _log(self, sym, side, qty, price, fee, reason, pnl, order_id):
        pnl_s = "" if pnl is None else f"{pnl:+.4f}"
        print(f"[{_now()}] {side} {sym} {qty} @ {price:.6g} fee {fee:.4f} ({reason}) "
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
        venue = getattr(self.client, "label", None) or (
            "BINANCE LIVE" if "api.binance.com" in self.client.base_url else "BINANCE TESTNET")
        mode = f"DRY RUN on {venue}" if self.dry_run else venue
        print(f"[{mode}] trading {', '.join(self.symbols)} on {self.interval} candles, "
              f"{self.trade_usdt:.2f} USDT per trade. Ctrl+C to stop; create "
              f"{self.guard.kill_file} to block new orders.")
        while True:
            self.step()
            time.sleep(poll)
