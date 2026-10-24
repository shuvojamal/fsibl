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

from tradebot.binance_client import LIVE_URL, BinanceClient, BinanceError, fill_summary
from tradebot.data import INTERVAL_MS, fetch_candles, ticker_price
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
                 capital=0.0, max_drawdown=0.0, pause_entries=False, max_price_gap=0.0,
                 require_fresh=False, backstop=0.0, close_now=(), rebuy_block_days=7,
                 savings=False, savings_keep=0.0):
        self.client, self.interval = client, interval
        self.engine = engine or EmaEngine(params)
        self.adopt = adopt  # treat coins already on the exchange as the bot's positions?
        self.max_open = max_open  # cap on simultaneous positions; 0 = no cap
        # Trade as if the account held only this much (plus the bot's own P&L),
        # whatever the exchange balance is. 0 = use the whole balance.
        self.capital = capital
        # Hard circuit breaker, independent of the strategy: once equity falls
        # this far below its peak, no new positions until a human resets it.
        # Exits keep working. 0 = off.
        self.max_drawdown = max_drawdown
        # Paused from the dashboard: no new positions, but stops and exits run.
        self.pause_entries = pause_entries
        # Bad-data guard, for buys only (exits never wait on it): skip a buy when
        # the exchange's price is more than this fraction away from Binance's
        # live price (signals come from Binance data, orders may go to OKX or a
        # testnet), or, with require_fresh, when the latest closed candle is
        # older than one interval.
        self.max_price_gap = max_price_gap
        self.require_fresh = require_fresh
        # Emergency backstop (research round 19): a real stop order resting on the
        # exchange this fraction below each position's stop, raised as the stop
        # trails. The daily-close stop still does the normal work; the backstop
        # only fires in a crash or if the bot doesn't run. 0 = off, and off on
        # clients without resting stop orders.
        self.backstop = backstop if hasattr(client, "place_stop") else 0.0
        # Sell requests from the dashboard: symbols, or "ALL". A coin sold this
        # way is not bought back for rebuy_block_days, or the next run would
        # often just re-enter on the same signal.
        self.close_now = [c.upper() for c in close_now]
        self.rebuy_block_days = rebuy_block_days
        # Auto savings (research round 32): spare USDT sits in Binance's flexible
        # savings between runs and earns interest; the bot takes out what a buy
        # needs just before buying and puts the spare back after each run.
        # Only on the live Binance exchange (the testnet and OKX demo have no
        # savings product). Turning it off moves the bot's deposits back to spot.
        # savings_keep: USDT always left on spot. A savings error never blocks
        # trading or exits: the run simply carries on with the spot balance.
        self.savings_wanted = savings
        self.savings_ok = hasattr(client, "earn_product") and getattr(client, "base_url", "") == LIVE_URL
        if savings and not self.savings_ok:
            print(f"[{_now()}] auto savings ignored: only available on the live Binance exchange")
        self.savings_keep = savings_keep
        self._product = None
        self.symbols = [s.upper() for s in symbols]
        self.trade_usdt, self.dry_run = trade_usdt, dry_run
        os.makedirs(state_dir, exist_ok=True)
        self.state_path = os.path.join(state_dir, "live_state.json")
        self.trades_path = os.path.join(state_dir, "live_trades.csv")
        self.fills_path = os.path.join(state_dir, "fills.csv")
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
        if self.savings_ok and self.savings_wanted:
            try:
                p, held = self._savings_product(), self.client.earn_balance("USDT")
                print(f"[{_now()}] auto savings on: {held:,.2f} USDT in flexible savings at {p['apr']:.2%} a year")
                usdt += held
            except (OSError, BinanceError) as e:
                print(f"[{_now()}] auto savings unavailable ({e}); trading from the spot balance only")
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
            if not self._backstop_filled(sym, self.state["positions"][sym]):
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
        freed = self._manual_closes()
        buys = []
        for sym in self.symbols:
            try:
                buy = self._step_symbol(sym)
                if buy:
                    buys.append(buy)
            except (OSError, BinanceError) as e:
                print(f"[{_now()}] {sym}: {type(e).__name__}: {e}")
        if freed:
            buys += self._refill_candidates({b[0] for b in buys})
        buys.sort(key=lambda b: -b[2].score)
        for sym, pos, plan, price in buys:
            try:
                self._open(sym, pos, plan, price)
            except (OSError, BinanceError) as e:
                print(f"[{_now()}] {sym}: {type(e).__name__}: {e}")
        self._sync_backstops()
        self._sweep_savings()
        self._record_equity()
        self._save()

    def _step_symbol(self, sym):
        pos = self.state["positions"][sym]
        if self._backstop_filled(sym, pos):
            return None
        candles = fetch_candles(sym, self.interval, self.engine.history)
        last = candles[-1]
        if last.open_time == pos["last_candle"]:
            return None
        pos["last_candle"] = last.open_time

        if pos["qty"] > 0:
            if last.low <= pos["stop"]:
                self._close(sym, pos, "stop_loss", ref=last.close)
                return None
            if last.high >= pos["target"]:
                self._close(sym, pos, "take_profit", ref=last.close)
                return None
            if hasattr(self.engine, "trail_stop"):
                new_stop = self.engine.trail_stop(candles, pos)
                if new_stop > pos["stop"]:
                    print(f"[{_now()}] {sym}: stop raised {pos['stop']:.4f} -> {new_stop:.4f}")
                    pos["stop"] = new_stop

        action = self.engine.decide(candles, pos["qty"] > 0)
        if action and action[0] == "buy":
            problem = self._bad_data(sym, last)
            if problem:
                print(f"[{_now()}] {sym}: BUY skipped, data check failed: {problem}")
                return None
            return (sym, pos, action[1], last.close)  # opened by step(), best score first
        if action and action[0] == "sell":
            self._close(sym, pos, action[1], ref=last.close)
        return None

    def _bad_data(self, sym, last):
        """Why the data behind a buy signal can't be trusted, or None if it looks fine."""
        if self.require_fresh:
            age = time.time() * 1000 - last.close_time
            if age > INTERVAL_MS[self.interval] * 1.05:
                return f"latest closed candle is {age / 3_600_000:.1f} h old (stale data)"
        if self.max_price_gap:
            # Compare the exchange with Binance's live price (where the signals come
            # from), not with the signal close: a coin that simply kept rising since
            # the close is not bad data, and research round 23 found that skipping
            # such "late" buys costs money.
            now = self.client.price(sym)
            try:
                ref = ticker_price(sym)
            except (OSError, ValueError, KeyError) as e:
                print(f"[{_now()}] {sym}: reference price unavailable ({e}); price check skipped")
                return None
            gap = now / ref - 1
            if abs(gap) > self.max_price_gap:
                return (f"exchange price {now:.6g} is {gap:+.1%} away from Binance's price {ref:.6g} "
                        f"(limit {self.max_price_gap:.0%}); the price data disagrees")
        return None

    def _record_equity(self):
        """Append one equity snapshot per run to equity.csv (used by the dashboard)."""
        try:
            eq = self._equity()
        except (OSError, BinanceError) as e:
            print(f"[{_now()}] equity snapshot skipped: {e}")
            return
        if self.max_drawdown:
            self.state["equity_peak"] = max(self.state.get("equity_peak", eq), eq)
        path = os.path.join(os.path.dirname(self.state_path), "equity.csv")
        new = not os.path.exists(path)
        open_n = sum(1 for p in self.state["positions"].values() if p["qty"] > 0)
        with open(path, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["time", "equity", "realised", "open_positions"])
            w.writerow([_now(), f"{eq:.2f}", f"{self.state.get('realised', 0.0):.2f}", open_n])

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
        total = self.client.balances().get("USDT", 0.0) + self._savings_balance()
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

    def drawdown_halted(self):
        """Update the equity peak; latch a halt if the drawdown limit is breached."""
        if self.state.get("halted"):
            return True
        if not self.max_drawdown:
            return False
        eq = self._equity()
        peak = max(self.state.get("equity_peak", eq), eq)
        self.state["equity_peak"] = peak
        if eq < peak * (1 - self.max_drawdown):
            self.state["halted"] = (f"{_now()}: equity {eq:,.2f} is {1 - eq / peak:.1%} below its peak "
                                    f"{peak:,.2f} (limit {self.max_drawdown:.0%})")
            print(f"[{_now()}] CIRCUIT BREAKER: {self.state['halted']}. New entries stopped; "
                  f"exits continue. Reset with --reset-halt after reviewing.")
            return True
        return False

    def _manual_closes(self):
        """Sell what the owner asked to sell from the dashboard, at market, now."""
        if not self.close_now:
            return 0
        freed = 0
        want = self.symbols if "ALL" in self.close_now else self.close_now
        for sym in want:
            pos = self.state["positions"].get(sym)
            if not pos or pos["qty"] <= 0:
                continue
            try:
                print(f"[{_now()}] {sym}: SELL requested from the dashboard")
                self._close(sym, pos, "manual", ref=self.client.price(sym))
                if pos["qty"] == 0:
                    freed += 1
                    until = time.time() * 1000 + self.rebuy_block_days * 86_400_000
                    self.state.setdefault("rebuy_blocked", {})[sym] = until
            except (OSError, BinanceError) as e:
                print(f"[{_now()}] {sym}: manual SELL failed: {type(e).__name__}: {e}")
        return freed

    def _refill_candidates(self, already):
        """After a sale by hand, today's buy signals can use the freed slots now.

        Coins whose latest daily candle was already processed earlier today are
        normally skipped until tomorrow's candle; this looks at them again, for
        buys only, so a freed slot doesn't sit empty for a day. The signal is
        the same one the strategy would have acted on this morning.
        """
        out = []
        for sym in self.symbols:
            pos = self.state["positions"][sym]
            if sym in already or pos["qty"] > 0:
                continue
            try:
                candles = fetch_candles(sym, self.interval, self.engine.history)
                last = candles[-1]
                if last.open_time != pos["last_candle"]:
                    continue                       # not processed yet: the normal pass handles it
                action = self.engine.decide(candles, False)
                if action and action[0] == "buy" and not self._bad_data(sym, last):
                    print(f"[{_now()}] {sym}: today's buy signal considered for a freed slot")
                    out.append((sym, pos, action[1], last.close))
            except (OSError, BinanceError) as e:
                print(f"[{_now()}] {sym}: {type(e).__name__}: {e}")
        return out

    def _open(self, sym, pos, plan, price):
        until = self.state.get("rebuy_blocked", {}).get(sym, 0)
        if until > time.time() * 1000:
            print(f"[{_now()}] {sym}: BUY skipped, sold by hand {self.rebuy_block_days} days ago or less")
            return
        if self.pause_entries:
            print(f"[{_now()}] {sym}: BUY skipped, bot is paused (exits still run)")
            return
        if self.drawdown_halted():
            print(f"[{_now()}] {sym}: BUY blocked: circuit breaker ({self.state['halted']})")
            return
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
        spend = self._cash_for(spend)
        if spend < self.client.symbol_filters(sym)["min_notional"]:
            print(f"[{_now()}] {sym}: BUY skipped, not enough USDT on spot ({spend:.2f})")
            return
        order = self.client.market_order(sym, "BUY", quote_qty=spend)
        qty, avg, fee = fill_summary(order)
        if qty == 0:
            print(f"[{_now()}] {sym}: BUY not filled ({order.get('status')})")
            return
        pos["qty"], pos["entry"] = qty, avg
        pos["stop"], pos["target"] = plan.stop, plan.target
        self._log(sym, "BUY", qty, avg, fee, why_buy, None, order.get("orderId"))
        self._log_fill(sym, "BUY", price, avg, qty * avg, fee)

    def _close(self, sym, pos, reason, ref=None):
        ok, why = self.guard.can_close()
        if not ok:
            print(f"[{_now()}] {sym}: SELL blocked: {why}")
            return
        if not self.dry_run and pos.get("backstop_id"):
            if self._backstop_filled(sym, pos):      # the exchange already sold it
                return
            self.client.cancel_stop(sym, pos["backstop_id"])   # frees the coins for the sell
            pos.pop("backstop_id", None); pos.pop("backstop_px", None)
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
        if ref:
            self._log_fill(sym, "SELL", ref, avg, qty * avg, fee)
        pos["qty"], pos["entry"], pos["stop"], pos["target"] = 0.0, 0.0, 0.0, 0.0

    # -- auto savings -----------------------------------------------------

    def _savings_product(self):
        if self._product is None:
            self._product = self.client.earn_product("USDT")
        return self._product

    def _savings_balance(self):
        if not self.savings_ok or not (self.savings_wanted or self.state.get("savings", {}).get("deposited")):
            return 0.0
        try:
            return self.client.earn_balance("USDT")
        except (OSError, BinanceError) as e:
            print(f"[{_now()}] savings balance unavailable ({e})")
            return 0.0

    def _cash_for(self, spend):
        """Make sure `spend` USDT is free on spot, taking it out of savings if needed.

        Returns what can actually be spent (less, if savings couldn't cover it).
        """
        if not (self.savings_ok and self.savings_wanted):
            return spend
        free = self.client.balances().get("USDT", 0.0)
        if free >= spend:
            return spend
        try:
            in_savings = self.client.earn_balance("USDT")
            amount = min(in_savings, (spend - free) * 1.002 + 0.01)
            if amount < 0.01:
                return min(spend, free)
            self.client.earn_redeem(self._savings_product()["id"], amount)
            sv = self.state.setdefault("savings", {})
            sv["deposited"] = max(0.0, sv.get("deposited", 0.0) - amount)
            print(f"[{_now()}] savings: took {amount:.2f} USDT out for a buy")
        except (OSError, BinanceError) as e:
            print(f"[{_now()}] savings: could not take USDT out ({e}); using the spot balance")
            return min(spend, free)
        for _ in range(10):                         # flexible redemptions usually land at once
            free = self.client.balances().get("USDT", 0.0)
            if free >= spend:
                break
            time.sleep(1)
        return min(spend, free)

    def _sweep_savings(self):
        """After the run: spare spot USDT into savings, or back out when switched off."""
        if not self.savings_ok:
            return
        sv = self.state.setdefault("savings", {})
        try:
            if not self.savings_wanted:
                back = min(sv.get("deposited", 0.0), self.client.earn_balance("USDT"))
                if back >= 0.01:
                    if self.dry_run:
                        print(f"[{_now()}] DRY RUN would move {back:.2f} USDT from savings back to spot")
                        return
                    self.client.earn_redeem(self._savings_product()["id"], back)
                    print(f"[{_now()}] savings switched off: moved {back:.2f} USDT back to spot")
                self.state.pop("savings", None)
                return
            p = self._savings_product()
            spare = self.client.balances().get("USDT", 0.0) - self.savings_keep
            if spare >= max(1.0, p["min"]) and p["can_buy"]:
                if self.dry_run:
                    print(f"[{_now()}] DRY RUN would move {spare:.2f} USDT into flexible savings "
                          f"({p['apr']:.2%} a year now)")
                else:
                    self.client.earn_subscribe(p["id"], spare)
                    sv["deposited"] = sv.get("deposited", 0.0) + spare
                    print(f"[{_now()}] savings: moved {spare:.2f} USDT in ({p['apr']:.2%} a year now)")
            sv.update(balance=round(self.client.earn_balance("USDT"), 2), apr=p["apr"], time=_now())
        except (OSError, BinanceError) as e:
            print(f"[{_now()}] savings skipped this run ({e}); trading is unaffected")

    # -- emergency backstop ----------------------------------------------

    def _backstop_filled(self, sym, pos):
        """If this position's resting backstop has fired, book the sale and return True."""
        algo = pos.get("backstop_id")
        if not algo or self.dry_run:
            return False
        try:
            state, order = self.client.stop_status(sym, algo)
        except (OSError, BinanceError) as e:
            print(f"[{_now()}] {sym}: backstop status unknown ({e}); will retry next run")
            return False
        if state == "live":
            return False
        trigger = pos.pop("backstop_px", None)
        pos.pop("backstop_id", None)
        if state != "filled":
            print(f"[{_now()}] {sym}: backstop order {algo} no longer resting; a new one will be placed")
            return False
        qty, avg, fee = fill_summary(order)
        pnl = qty * (avg - pos["entry"]) - fee
        self.guard.record(pnl)
        self.state["realised"] = self.state.get("realised", 0.0) + pnl
        print(f"[{_now()}] {sym}: EMERGENCY BACKSTOP fired on the exchange")
        self._log(sym, "SELL", qty, avg, fee, "backstop", pnl, order.get("orderId"))
        if trigger:
            self._log_fill(sym, "SELL", trigger, avg, qty * avg, fee)
        left = pos["qty"] - qty
        if left > 1e-12 and left * avg >= self.client.symbol_filters(sym)["min_notional"]:
            pos["qty"] = left                       # partial fill: keep managing the rest
            return False
        pos["qty"], pos["entry"], pos["stop"], pos["target"] = 0.0, 0.0, 0.0, 0.0
        return True

    def _sync_backstops(self):
        """Place a backstop for every open position, and raise it when the stop rose."""
        if not self.backstop or self.dry_run:
            return
        for sym in self.symbols:
            pos = self.state["positions"][sym]
            if pos["qty"] <= 0 or pos.get("stop", 0) <= 0:
                continue
            want = pos["stop"] * (1 - self.backstop)
            have = pos.get("backstop_px")
            if have and want <= have * 1.001:
                continue                            # unchanged (stops only ever rise)
            try:
                if pos.get("backstop_id"):
                    self.client.cancel_stop(sym, pos["backstop_id"])
                    pos.pop("backstop_id"); pos.pop("backstop_px", None)
                pos["backstop_id"] = self.client.place_stop(sym, pos["qty"], want)
                pos["backstop_px"] = want
                print(f"[{_now()}] {sym}: backstop {'raised' if have else 'placed'} at {want:.6g} "
                      f"({self.backstop:.0%} below the stop {pos['stop']:.6g})")
            except (OSError, BinanceError) as e:
                print(f"[{_now()}] {sym}: backstop not placed ({e}); the daily-close stop still applies")

    def _log_fill(self, sym, side, ref, fill, notional, fee):
        """Execution quality: how far the real fill was from the close the decision used.

        The backtest assumes fills at that price (plus 0.05% slippage and the
        0.1% fee), so a growing gap here means live results will trail it.
        Positive slippage is a worse price: paid more on a buy, got less on a sell.
        """
        slip = fill / ref - 1 if side == "BUY" else 1 - fill / ref
        new = not os.path.exists(self.fills_path)
        with open(self.fills_path, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["time", "symbol", "side", "signal_price", "fill_price", "slippage_pct", "fee_pct"])
            w.writerow([_now(), sym, side, f"{ref:.8g}", f"{fill:.8g}", f"{slip * 100:.4f}",
                        f"{fee / notional * 100 if notional else 0:.4f}"])

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
