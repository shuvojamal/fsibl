"""Round 12b: is the ADX trend filter (and top-10 universe) robust, or a full-
period fit? Evaluate each variant separately on the first and second half
of the 2017-2026 history, plus each bear year. A rule worth adopting must
help in both halves."""
import os as _os
import sys
HERE = _os.path.dirname(_os.path.abspath(__file__))
ns = {'__file__': _os.path.join(HERE, 'research12.py')}
src = open(_os.path.join(HERE, 'research12.py')).read().split("L = []")[0]
exec(src, ns)
run, metrics, ADXFiltered, OppParams, Opportunity, t0, tN = (ns[k] for k in
    ('run', 'metrics', 'ADXFiltered', 'OppParams', 'Opportunity', 't0', 'tN'))
from datetime import datetime, timezone
ms = lambda y, mth=1: int(datetime(y, mth, 1, tzinfo=timezone.utc).timestamp() * 1000)
mid = t0 + (tN - t0) // 2
WINDOWS = [("1st half 2017-08..2022-03", t0, mid), ("2nd half 2022-03..2026-10", mid, None),
           ("2018 (bear)", ms(2018), ms(2019)), ("2022 (bear)", ms(2022), ms(2023)),
           ("2025-26 (chop)", ms(2025), None)]
VARIANTS = [("baseline (top 15)", {}),
            ("ADX > 20", dict(make=lambda: ADXFiltered(OppParams(), 20))),
            ("ADX > 25", dict(make=lambda: ADXFiltered(OppParams(), 25))),
            ("ADX > 30", dict(make=lambda: ADXFiltered(OppParams(), 30))),
            ("top 10", dict(top=10)),
            ("top 10 + ADX > 25", dict(top=10, make=lambda: ADXFiltered(OppParams(), 25)))]
L = ["Each cell: return / max drawdown / Sharpe / expectancy R. Indicators warm up on all prior data.\n",
     f"{'variant':20} | " + " | ".join(f"{w[0]:>30}" for w in WINDOWS)]
for name, kw in VARIANTS:
    cells = []
    for _, a, b in WINDOWS:
        m = metrics(*run(start=a, end=b, **kw))
        cells.append(f"{m['ret']:+7.1%} {m['dd']:6.1%} {m['sharpe']:5.2f} {m['exp_r']:+.2f}R")
    L.append(f"{name:20} | " + " | ".join(f"{c:>30}" for c in cells))
out = "\n".join(L) + "\n"
open(_os.path.join(HERE, '..', 'results', 'research12b.out'), 'w').write(out)
print(out)
