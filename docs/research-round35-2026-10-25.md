# Research round 35: the risk profile of steady vs growth (scheduled daily run)

**Question.** Before real money: how do the bad stretches look? Worst day,
week and month; how long the account stays below its previous high; how
often months and years lose.

**Method.** Steady (8 × 0.5%) and growth (8 × 1%), 6 of 8 checks, top 15,
round 12's simulator and costs, round 21's six close times × two halves.
Median cell and worst cell reported (`research/results/research35.out`).

**Pass bar (set before running), a suitability test:** fit for a first
real-money account if, in its worst cell, the worst 30 days are no deeper
than −20%, the longest time below a previous high is at most 18 months, and
no calendar year loses more than 15%.

| (worst cell of 12) | steady 0.5% | growth 1% |
|---|---|---|
| worst day | −10.9% | −18.3% |
| worst 7 days | −12.6% | −21.7% |
| worst 30 days | −13.7% ✅ | −23.5% ❌ |
| longest below previous high | 653 days (21 months) ❌ | 652 days (21 months) ❌ |
| worst calendar year | −10.3% ✅ | −19.9% ❌ |
| losing months, 2022-26 (median) | 57% | 57% |
| time >10% below the high, 2022-26 (median) | 37% | 72% |

Calendar years (median close time), steady: 2018 −2%, 2019 +19%, 2020 +41%,
2021 +67%, 2022 −7%, 2023 +35%, 2024 +41%, 2025 −5%, 2026 so far +15%.
Growth: roughly double each figure, both ways.

**Verdict: neither passes the bar as set**, both because of one stretch:
from early 2022 to late 2023 the account stayed below its high for about
21 months (the 2022 bear market, then a flat 2023 until its year-end rally).
That is a property of trend following, not of the risk level: the length
is the same for steady and growth.

**What it means for the owner:**
- Steady passes the loss tests comfortably (worst month −14%, worst year
  −10%); growth fails them (worst month −24%, worst year −20%, and it spent
  72% of 2022-26 more than 10% below its high).
- More months lose than win (57% in 2022-26). The profit comes from a few
  strong months. Judging the bot month by month will feel bad most of the time.
- Plan for up to about two years without a new high.
- **Recommendation (no setting changed):** start real money with steady, and
  only money that can sit untouched for 2+ years. Consider growth only after
  steady has run live for a while. The idle-cash savings (round 32) helps
  most in exactly these flat stretches.
