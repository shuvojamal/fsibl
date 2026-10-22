"""Round 7b: is dropping the RSI-zone check a real improvement, or an artifact of
a looser threshold? Test on 20 coins AND on each 10-coin half separately."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
OUT = _os.path.join(HERE, '..', 'data')      # cached candles
RES = _os.path.join(HERE, '..', 'results')   # tables written here
import pickle, sys
sys.path.insert(0, ROOT)
sys.argv = ['x']
from tradebot.opportunity import Opportunity, OppParams
orig = pickle.load(open(f'{OUT}/daily10.pkl', 'rb')); new = pickle.load(open(f'{OUT}/daily_new10.pkl', 'rb'))
import importlib.util
spec = importlib.util.spec_from_file_location('r7', f'{HERE}/research7.py')
# reuse research7's portfolio() without re-running its experiments: exec only the needed defs
src = open(f'{HERE}/research7.py').read().split("WINDOWS = ")[0]
ns = {'__file__': _os.path.join(HERE, 'research7.py')}
exec(src, ns)
portfolio, Ablated = ns['portfolio'], ns['Ablated']


class NoRSI(Opportunity):
    """Seven checks, RSI zone removed outright; threshold is min_score of 7."""
    CHECKS = 7
    def checks(self, i):
        cs = super().checks(i)
        return None if cs is None else [(n, ok) for n, ok in cs if n != 'rsi_zone']


class WideRSI(Opportunity):
    def __init__(self, p, lo, hi):
        super().__init__(OppParams(**{**p.__dict__, 'rsi_lo': lo, 'rsi_hi': hi}))


VARIANTS = {
    'baseline 5 of 8 (RSI 45-65 required)': lambda: Opportunity(OppParams()),
    'RSI always passes (= 4 of other 7)': lambda: Ablated(OppParams(), 'rsi_zone'),
    'RSI removed, 5 of 7': lambda: NoRSI(OppParams(min_score=5)),
    'RSI removed, 4 of 7': lambda: NoRSI(OppParams(min_score=4)),
    'RSI zone widened 40-80, 5 of 8': lambda: WideRSI(OppParams(), 40, 80),
    'RSI zone 50-80 (momentum), 5 of 8': lambda: WideRSI(OppParams(), 50, 80),
}
WINDOWS = [(0.0, 'full 4y'), (0.5, 'from 2024-10'), (0.7, 'from 2025-07'), (0.8, 'from 2025-12')]
lines = []
for uni_name, uni in (('ALL 20 COINS', {**orig, **new}), ('ORIGINAL 10', orig), ('OTHER 10', new)):
    ns['data'] = uni
    lines.append(f"\n### {uni_name} (max 5 open, 1% risk). Cells: return, max DD, trades, PF\n")
    lines.append(f"{'variant':38} | " + " | ".join(f"{l:>25}" for _, l in WINDOWS))
    for name, make in VARIANTS.items():
        cells = []
        for w, _ in WINDOWS:
            r = portfolio(make, start_frac=w)
            cells.append(f"{r['ret']:+7.1%} {r['dd']:6.1%} {r['n']:4}t {r['pf']:4.2f}")
        lines.append(f"{name:38} | " + " | ".join(cells))
open(f'{RES}/research7b.md', 'w').write("\n".join(lines) + "\n")
print("\n".join(lines))
