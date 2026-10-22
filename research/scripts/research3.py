"""Research round 3: exits and sizing for the opportunity scorer (daily, 10 coins).
  A. Trailing (chandelier) stop instead of a fixed 3:1 target: let winners run.
  B. Volatility-scaled risk: risk less of equity when the market is wild.
Judged on the fixed universal entry setting (score 5, 2 ATR stop) across the
four test windows AND the full history, so a result has to hold up everywhere.
"""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')      # cached candles
RES = _os.path.join(HERE, '..', 'results')   # tables written here
import pickle, sys
sys.path.insert(0, ROOT)
from tradebot import backtest
from tradebot.opportunity import Opportunity, OppParams
from datetime import datetime, timezone

daily = pickle.load(open(f'{OUT}/daily10.pkl', 'rb'))
d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m-%d')
BASE = dict(min_score=5, stop_atr=2.0, reward_risk=3.0)


class Trailing(Opportunity):
    """Chandelier exit: stop = highest close since entry - trail_atr * ATR.
    Target is removed (set far away) so the trail decides the exit."""
    def __init__(self, p, trail_atr=3.0, keep_target=False):
        super().__init__(p)
        self.trail_atr, self.keep_target = trail_atr, keep_target
        self.hi = None
    def signal(self, i):
        plan = super().signal(i)
        if plan:
            self.hi = self.closes[i]
            if not self.keep_target:
                plan.target = self.closes[i] * 1000
        return plan
    def update_stop(self, i, stop):
        self.hi = max(self.hi or 0, self.closes[i])
        return self.hi - self.trail_atr * self.atr[i]
    def should_exit(self, i):
        return False  # the trail replaces the EMA-cross exit


class VolScaled(Opportunity):
    """Risk risk_frac of equity when ATR% is at its typical level, less when
    volatility is above it (risk * typical/current, capped at 1x)."""
    def __init__(self, p, typical=0.03):
        super().__init__(p); self.typical = typical; self._vol = None
    def signal(self, i):
        plan = super().signal(i)
        if plan:
            self._vol = self.atr[i] / self.closes[i]
        return plan
    def size(self, equity, price, stop):
        scale = min(1.0, self.typical / self._vol) if self._vol else 1.0
        r = price - stop
        return min(equity * self.p.risk_frac * scale / r, equity / price) if r > 0 else 0.0


VARIANTS = {
    'baseline (3:1 target + EMA exit)': lambda: Opportunity(OppParams(**BASE)),
    'trail 2 ATR': lambda: Trailing(OppParams(**BASE), 2.0),
    'trail 3 ATR': lambda: Trailing(OppParams(**BASE), 3.0),
    'trail 4 ATR': lambda: Trailing(OppParams(**BASE), 4.0),
    'trail 3 ATR + keep 3:1 target': lambda: Trailing(OppParams(**BASE), 3.0, keep_target=True),
    'vol-scaled risk (typical 2%)': lambda: VolScaled(OppParams(**BASE), 0.02),
    'vol-scaled risk (typical 3%)': lambda: VolScaled(OppParams(**BASE), 0.03),
}
WINDOWS = [0.5, 0.6, 0.7, 0.8, 0.0]  # 0.0 = full history

lines = ["Daily, 10 coins, entry setting fixed (score 5, 2 ATR stop). Cells: average return across coins / coins profitable.\n"]
hdr = f"{'variant':32} | " + " | ".join(
    (f"{'full 4y':>13}" if w == 0.0 else f"{'from ' + d(daily['BTCUSDT'][int(len(daily['BTCUSDT'])*w)].open_time)[:7]:>13}") for w in WINDOWS) + f" | {'avg maxDD':>9}"
lines.append(hdr)
for name, make in VARIANTS.items():
    cells, dds = [], []
    for w in WINDOWS:
        rets = []
        for s, cs in daily.items():
            split = int(len(cs) * w)
            r = backtest.run_opportunity(cs[split:], make())
            rets.append(r.total_return)
            if w == 0.0:
                dds.append(r.max_drawdown)
        cells.append(f"{sum(rets)/10:+6.1%} {sum(x > 0 for x in rets):>2}/10")
    lines.append(f"{name:32} | " + " | ".join(cells) + f" | {sum(dds)/10:9.1%}")

lines.append("\nFull-history detail for the trailing-stop variants (per coin):")
for name in ('baseline (3:1 target + EMA exit)', 'trail 3 ATR', 'trail 4 ATR'):
    lines.append(f"\n  {name}")
    for s, cs in daily.items():
        r = backtest.run_opportunity(cs, VARIANTS[name]())
        big = max((t.ret for t in r.trades), default=0)
        lines.append(f"    {s:9} {r.total_return:+7.1%}  trades {len(r.trades):3}  win {r.win_rate:4.0%}  "
                     f"PF {min(r.profit_factor, 99):5.2f}  maxDD {r.max_drawdown:6.1%}  best trade {big:+6.1%}")
open(f'{RES}/research3.md', 'w').write("\n".join(lines) + "\n")
print("\n".join(lines))
