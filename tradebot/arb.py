"""Cross-exchange arbitrage scanner and paper trader.

Every few seconds, fetch the best bid and ask for each symbol on every
exchange. If one exchange's bid is higher than another's ask by more than
both taker fees, that's a gap: buy on the cheap one, sell on the dear one.

Paper mode assumes you already hold USDT on every exchange and the coin on
every exchange (so you can sell without first transferring, which takes
minutes and costs a withdrawal fee). Trades are sized to the smaller of the
two top-of-book quantities, so we only ever claim what was actually there.
"""
import csv
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from tradebot.exchanges import EXCHANGES


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def fetch_all(symbols, exchanges):
    """Return {symbol: [Quote, ...]} and a list of (exchange, symbol, error)."""
    quotes, errors = {s: [] for s in symbols}, []
    jobs = [(ex, sym) for sym in symbols for ex in exchanges]
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        results = pool.map(lambda j: _safe(EXCHANGES[j[0]][0], j[1]), jobs)
    for (ex, sym), r in zip(jobs, results):
        (quotes[sym].append if not isinstance(r, Exception) else
         lambda e: errors.append((ex, sym, e)))(r)
    return quotes, errors


def _safe(fn, sym):
    try:
        return fn(sym)
    except Exception as e:  # noqa: BLE001 - one bad feed must not stop the others
        return e


def best_gap(quotes):
    """The widest buy-low/sell-high pair among these quotes, or None."""
    best = None
    for buy in quotes:
        for sell in quotes:
            if buy.exchange == sell.exchange or buy.ask <= 0:
                continue
            gross = sell.bid / buy.ask - 1
            net = gross - EXCHANGES[buy.exchange][1] - EXCHANGES[sell.exchange][1]
            if best is None or net > best["net"]:
                best = {"buy": buy, "sell": sell, "gross": gross, "net": net,
                        "qty": min(buy.ask_qty, sell.bid_qty)}
    return best


class ArbScanner:
    def __init__(self, symbols, exchanges, capital, log_dir, min_net=0.0):
        self.symbols = [s.upper() for s in symbols]
        self.exchanges, self.capital, self.min_net = exchanges, capital, min_net
        os.makedirs(log_dir, exist_ok=True)
        self.scan_path = os.path.join(log_dir, "scans.csv")
        self.trade_path = os.path.join(log_dir, "arb_trades.csv")
        self.scans = self.opportunities = 0
        self.pnl = 0.0

    def step(self):
        quotes, errors = fetch_all(self.symbols, self.exchanges)
        for ex, sym, e in errors:
            print(f"[{_now()}] {ex} {sym}: {type(e).__name__}: {e}")
        self.scans += 1
        for sym in self.symbols:
            g = best_gap(quotes[sym])
            if g is None:
                continue
            self._csv(self.scan_path, ["time", "symbol", "buy_on", "ask", "sell_on", "bid",
                                       "gross_gap", "net_gap", "qty"],
                      [_now(), sym, g["buy"].exchange, g["buy"].ask, g["sell"].exchange,
                       g["sell"].bid, f"{g['gross']:.6f}", f"{g['net']:.6f}", g["qty"]])
            tag = "GAP " if g["net"] > self.min_net else "    "
            print(f"[{_now()}] {tag}{sym:9} buy {g['buy'].exchange:8} {g['buy'].ask:>12.4f}"
                  f"  sell {g['sell'].exchange:8} {g['sell'].bid:>12.4f}"
                  f"  gross {g['gross']*100:+.3f}%  net {g['net']*100:+.3f}%")
            if g["net"] > self.min_net:
                self._paper_trade(sym, g)

    def _paper_trade(self, sym, g):
        qty = min(g["qty"], self.capital / g["buy"].ask)
        profit = qty * g["buy"].ask * g["net"]
        self.pnl += profit
        self.opportunities += 1
        self._csv(self.trade_path, ["time", "symbol", "buy_on", "sell_on", "qty", "net_gap", "profit_usdt"],
                  [_now(), sym, g["buy"].exchange, g["sell"].exchange, f"{qty:.8f}",
                   f"{g['net']:.6f}", f"{profit:.4f}"])
        print(f"[{_now()}]      -> paper trade {qty:.6f} {sym}: {profit:+.4f} USDT")

    @staticmethod
    def _csv(path, header, row):
        new = not os.path.exists(path)
        with open(path, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(header)
            w.writerow(row)

    def run(self, seconds=None, poll=3):
        start = time.time()
        print(f"Scanning {', '.join(self.symbols)} across {', '.join(self.exchanges)} "
              f"every {poll}s. Ctrl+C to stop.")
        try:
            while seconds is None or time.time() - start < seconds:
                self.step()
                time.sleep(poll)
        except KeyboardInterrupt:
            pass
        print(f"\n{self.scans} scans, {self.opportunities} net-positive gaps, "
              f"paper profit {self.pnl:+.4f} USDT on {self.capital:.0f} USDT per leg")
