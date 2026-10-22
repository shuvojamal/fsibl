"""Command-line entry point: python -m tradebot <command> ..."""
import argparse
from datetime import datetime, timezone

from tradebot import backtest
from tradebot.data import fetch_candles
from tradebot.arb import ArbScanner
from tradebot.exchanges import EXCHANGES
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


def _params(a):
    return Params(fast=a.fast, slow=a.slow, rsi_max=a.rsi_max,
                  stop_loss=a.stop_loss, take_profit=a.take_profit)


def main():
    ap = argparse.ArgumentParser(prog="tradebot", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--interval", default="1h")
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

    a = ap.parse_args()
    if a.cmd == "backtest":
        for sym in a.symbols:
            candles = fetch_candles(sym, a.interval, a.candles)
            _report(f"{sym.upper()} {a.interval}", backtest.run(candles, _params(a)), candles)
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
        PaperTrader(a.symbols, a.interval, _params(a), a.capital, a.state_dir).run_forever()
    elif a.cmd == "arb":
        ArbScanner(a.symbols, a.exchanges, a.capital, a.log_dir, a.min_net).run(a.seconds, a.poll)


if __name__ == "__main__":
    main()
