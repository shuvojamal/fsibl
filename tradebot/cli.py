"""Command-line entry point: python -m tradebot <command> ..."""
import argparse
from datetime import datetime, timezone

from tradebot import backtest
from tradebot.data import fetch_candles
from tradebot.arb import ArbScanner
from tradebot.exchanges import EXCHANGES
from tradebot.binance_client import LIVE_URL, TESTNET_URL, BinanceClient
from tradebot.engines import make_engine
from tradebot.live import LiveTrader
from tradebot.okx_client import OKXClient
from tradebot.opportunity import Opportunity, OppParams
from tradebot.paper import PaperTrader
from tradebot.strategy import Params


def _date(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d")


def _report(title, res, candles):
    print(f"\n== {title}: {_date(candles[0].open_time)} -> {_date(candles[-1].close_time)} ==")
    print(f"  trades           {len(res.trades)}")
    print(f"  win rate         {res.win_rate:.1%}")
    print(f"  avg win / loss   {res.avg_win:+.2%} / {res.avg_loss:+.2%}")
    print(f"  profit factor    {res.profit_factor:.2f}   (above 1.0 = made money)")
    print(f"  strategy return  {res.total_return:+.2%}")
    print(f"  buy & hold       {res.buy_hold_return:+.2%}")
    print(f"  max drawdown     {res.max_drawdown:.2%}")


def _opp(a):
    return OppParams(min_score=a.min_score, risk_frac=a.risk)


def _engine(a):
    return make_engine(a.strategy, _params(a), _opp(a))


def _run_backtest(a, candles):
    if a.strategy == "opportunity":
        return backtest.run_opportunity(candles, Opportunity(_opp(a)))
    return backtest.run(candles, _params(a))


def _params(a):
    return Params(fast=a.fast, slow=a.slow, rsi_max=a.rsi_max,
                  stop_loss=a.stop_loss, take_profit=a.take_profit)


def main():
    ap = argparse.ArgumentParser(prog="tradebot", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--interval", default="1h")
        p.add_argument("--strategy", choices=["ema", "opportunity"], default="ema",
                       help="ema: crossover; opportunity: trade only when enough checks agree")
        p.add_argument("--min-score", type=int, default=5, help="opportunity: checks required, of 8")
        p.add_argument("--risk", type=float, default=0.01, help="opportunity: equity fraction risked per trade")
        p.add_argument("--fast", type=int, default=12)
        p.add_argument("--slow", type=int, default=26)
        p.add_argument("--rsi-max", type=float, default=70)
        p.add_argument("--stop-loss", type=float, default=0.03)
        p.add_argument("--take-profit", type=float, default=0.06)

    bt = sub.add_parser("backtest", help="test the strategy on past data")
    bt.add_argument("symbols", nargs="+")
    bt.add_argument("--candles", type=int, default=5000)
    common(bt)

    op = sub.add_parser("optimize", help="tune parameters, then check them on unseen data")
    op.add_argument("symbols", nargs="+")
    op.add_argument("--candles", type=int, default=5000)
    op.add_argument("--interval", default="1h")

    pp = sub.add_parser("paper", help="trade live prices with fake money")
    pp.add_argument("symbols", nargs="+")
    pp.add_argument("--capital", type=float, default=1000)
    pp.add_argument("--state-dir", default="paper_state")
    common(pp)

    ar = sub.add_parser("arb", help="scan exchanges for price gaps and paper-trade them")
    ar.add_argument("symbols", nargs="+")
    ar.add_argument("--exchanges", nargs="+", default=list(EXCHANGES), choices=list(EXCHANGES))
    ar.add_argument("--capital", type=float, default=1000, help="USDT available per leg")
    ar.add_argument("--seconds", type=int, default=None, help="stop after this long")
    ar.add_argument("--poll", type=int, default=3)
    ar.add_argument("--min-net", type=float, default=0.0,
                    help="only trade gaps above this net fraction, e.g. 0.001 = 0.1%%")
    ar.add_argument("--log-dir", default="arb_logs")

    lv = sub.add_parser("live", help="trade a Binance account (testnet by default)")
    lv.add_argument("symbols", nargs="+")
    lv.add_argument("--trade-usdt", type=float, default=20, help="USDT spent per buy")
    lv.add_argument("--max-trade-usdt", type=float, default=50,
                    help="risk guard: refuse any single buy above this")
    lv.add_argument("--max-daily-loss", type=float, default=20,
                    help="risk guard: stop opening trades after losing this much in a day")
    lv.add_argument("--kill-file", default="STOP", help="create this file to block new orders")
    lv.add_argument("--state-dir", default="live_state")
    lv.add_argument("--exchange", choices=["binance", "okx"], default="binance",
                    help="binance: Spot Testnet / live; okx: demo trading / live")
    lv.add_argument("--max-open", type=int, default=0,
                    help="cap on simultaneous open positions across all symbols (0 = no cap)")
    lv.add_argument("--once", action="store_true",
                    help="check every symbol once, save state, and exit (for a scheduled job)")
    lv.add_argument("--no-adopt", action="store_true",
                    help="leave coins already in the account alone instead of managing them as positions")
    lv.add_argument("--dry-run", action="store_true", help="connect and decide, but place no orders")
    lv.add_argument("--live", action="store_true",
                    help="use the real exchange instead of the testnet (real money)")
    lv.add_argument("--i-accept-the-risk", action="store_true",
                    help="required together with --live")
    common(lv)

    sc = sub.add_parser("scan", help="rank a coin pool by 90-day volume and show today's signals")
    sc.add_argument("--top", type=int, default=15, help="keep the N most-traded coins (default 15)")
    sc.add_argument("--pool", nargs="+", default=None, help="coins to consider (default: built-in 40)")
    sc.add_argument("--symbols-only", action="store_true",
                    help="print just the top-N symbols, space-separated, for pasting into `live`")

    rp = sub.add_parser("report", help="one-screen status of a live/demo run")
    rp.add_argument("symbols", nargs="+")
    rp.add_argument("--exchange", choices=["binance", "okx", "none"], default="okx",
                    help="none: skip the account section (no keys needed)")
    rp.add_argument("--live", action="store_true")
    rp.add_argument("--state-dir", default="okx_opp")
    rp.add_argument("--interval", default="1d")

    to = sub.add_parser("test-order", help="prove order routing: market-buy a small amount, then sell it back")
    to.add_argument("symbol")
    to.add_argument("--usdt", type=float, default=20)
    to.add_argument("--exchange", choices=["binance", "okx"], default="okx")
    to.add_argument("--live", action="store_true")
    to.add_argument("--i-accept-the-risk", action="store_true")

    a = ap.parse_args()
    if a.cmd == "backtest":
        for sym in a.symbols:
            candles = fetch_candles(sym, a.interval, a.candles)
            _report(f"{sym.upper()} {a.interval} [{a.strategy}]", _run_backtest(a, candles), candles)
    elif a.cmd == "optimize":
        for sym in a.symbols:
            candles = fetch_candles(sym, a.interval, a.candles)
            found = backtest.optimize(candles)
            if found is None:
                print(f"{sym.upper()}: not enough trades to optimize")
                continue
            p, train, test = found
            split = len(train.equity)
            print(f"\n### {sym.upper()} best params on training data: {p}")
            _report("training (used for tuning)", train, candles[:split])
            _report("unseen data (the honest number)", test, candles[split:])
    elif a.cmd == "paper":
        PaperTrader(a.symbols, a.interval, _params(a), a.capital, a.state_dir,
                    engine=_engine(a)).run_forever()
    elif a.cmd == "live":
        if a.live and not a.i_accept_the_risk:
            ap.error("--live places real orders with real money; add --i-accept-the-risk "
                     "if that is what you want")
        if a.exchange == "okx":
            client = OKXClient(demo=not a.live)
        else:
            client = BinanceClient(base_url=LIVE_URL if a.live else TESTNET_URL)
        trader = LiveTrader(client, a.symbols, a.interval, _params(a), a.trade_usdt,
                            (a.max_trade_usdt, a.max_daily_loss, a.kill_file), a.state_dir,
                            dry_run=a.dry_run, engine=_engine(a), adopt=not a.no_adopt,
                            max_open=a.max_open)
        trader.preflight()
        if a.once:
            trader.step()
        else:
            trader.run_forever()
    elif a.cmd == "scan":
        from tradebot.scan import POOL, format_scan, scan
        rows, skipped = scan(a.pool or POOL, a.top)
        if a.symbols_only:
            print(" ".join(r[0] for r in rows))
        else:
            print("\n".join(format_scan(rows)))
            if skipped:
                print(f"\nskipped (no data or too short): {', '.join(skipped)}")
    elif a.cmd == "report":
        from tradebot.report import report
        if a.exchange == "none":
            client = None
        elif a.exchange == "okx":
            client = OKXClient(demo=not a.live)
        else:
            client = BinanceClient(base_url=LIVE_URL if a.live else TESTNET_URL)
        print("\n".join(report(client, a.state_dir, [s.upper() for s in a.symbols], a.interval)))
    elif a.cmd == "test-order":
        if a.live and not a.i_accept_the_risk:
            ap.error("--live places real orders with real money; add --i-accept-the-risk")
        from tradebot.binance_client import fill_summary
        client = OKXClient(demo=not a.live) if a.exchange == "okx" else \
            BinanceClient(base_url=LIVE_URL if a.live else TESTNET_URL)
        sym = a.symbol.upper()
        print(f"venue: {getattr(client, 'label', client.base_url)}")
        print(f"balances before: {client.balances()}")
        buy = client.market_order(sym, "BUY", quote_qty=a.usdt)
        qty, avg, fee = fill_summary(buy)
        print(f"BUY  order {buy['orderId']}: {qty} {sym} @ {avg:.4f}, fee {fee:.6f}, status {buy['status']}")
        sell = client.market_order(sym, "SELL", qty=qty)
        sq, sa, sf = fill_summary(sell)
        print(f"SELL order {sell['orderId']}: {sq} {sym} @ {sa:.4f}, fee {sf:.6f}, status {sell['status']}")
        print(f"round trip: {sq * sa - qty * avg - fee - sf:+.4f} USDT (fees + spread)")
        print(f"balances after: {client.balances()}")
    elif a.cmd == "arb":
        ArbScanner(a.symbols, a.exchanges, a.capital, a.log_dir, a.min_net).run(a.seconds, a.poll)


if __name__ == "__main__":
    main()
