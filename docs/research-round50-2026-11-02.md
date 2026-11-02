# Research round 50: is the edge still more than luck after 49 rounds? (scheduled daily run)

**Question.** Every variant tried raises the "luck bar": the best of many
random strategies looks good by chance. Round 16 checked the live rules
assuming ~300 variants; rounds 17-49 added roughly 300 more, and the
current set-ups (8 slots, 6 of 8 checks) are different. Does the edge still
clear the bar?

**Method.** Round 16's deflated Sharpe ratio (Bailey & López de Prado),
unchanged: daily returns of steady and growth on round 12's 55-coin data,
2017-08 .. 2026-10; trial-to-trial spread from 13 nearby variants (risk,
slots, checks, trail), and round 16's conservative spread × 4; N swept.
Pass bar (set first): steady's DSR at least 0.95 at N = 600 with the
variant spread.

**Result** (`research/results/research50.out`):
- Steady: Sharpe 1.08; DSR 0.988 at N = 600 (0.891 with spread × 4).
- Growth: Sharpe 1.10; DSR 0.990 at N = 600 (0.905 with spread × 4).
**Passes.**

**Meaning.** Even after all the searching, the probability that the
current set-ups' backtest edge is real rather than luck is about 0.99 on
the main measure, and about 0.9 on the deliberately harsh one. What the
test does not cover: the survivorship and hindsight haircuts (dead coins
missing, today's coin list), which are why the planning numbers already
use a realistic drag below the backtest (rounds 25/36).
