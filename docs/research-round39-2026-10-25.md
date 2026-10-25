# Research round 39: can the 1999-2025 DSE dataset extend the DSE test?

The owner shared "Dhaka Stock Exchange Historical Data (1999-2025)",
Mendeley Data, doi:10.17632/5mww8rb9td.1, CC BY 4.0 (531 instruments,
1999-01 .. 2025-04). The extra 1999-2012 years, including the 2010 bubble
and crash, would make a valuable extra test of round 38.

**Problem.** The prices are not adjusted for bonus shares: ACI falls from
147.8 to 127.0 on its 15% bonus (2024-11-18). In a backtest, each bonus
looks like a crash and triggers a stop that never happened.

**Test.** Detect bonuses from the data itself (a record-date row with
open = 0 and volume = 0, followed by a drop of more than 5%), checked
against the true adjustments from round 38's adjusted dataset, 2012-2025.
Pass bar (set first): finds at least 90% of real events with few false alarms.

**Result** (`research/results/research39.out`): found 29 of 1,236 real
events (2%), with 140 false alarms. The record-date marker rows exist only
from 2023 onward; before that the data gives no way to tell a bonus from a
real fall. **Fails.**

**Verdict.** This dataset can't be used for a stop-based strategy test
before 2023 without corporate-action records. Round 38's adjusted 2012-2026
data remains the basis; its rejection stands. The dataset was not cached.
