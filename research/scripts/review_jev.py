"""Review of github.com/zadescoxp/Jev-Trades (2026-10-23): what its own saved paper trades show.

Reads the SQLite database committed in that repo (pipeline/jev_trades.db)
read-only and summarises the agent's decisions and trades, then re-prices the
trades with a realistic 0.1% fee per side (the repo's paper broker charges 0).
Usage: python research/scripts/review_jev.py /path/to/jev-trades/pipeline/jev_trades.db
"""
import sqlite3
import sys

db = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
ts = [r[0] for r in db.execute("select timestamp from agent_decisions order by 1")]
print(f"decisions: {len(ts)} over {(ts[-1] - ts[0]) / 3600:.1f} hours, timeframes {db.execute('select group_concat(distinct timeframe) from agent_decisions').fetchone()[0]}")
for reason, ex, n in db.execute("select reason, executed, count(*) from agent_decisions group by 1, 2"):
    print(f"  {reason:5s} executed={ex}  {n}")
rows = db.execute("select side, qty, price, source, realized_pnl from trades order by id").fetchall()
pairs = [(rows[i], rows[i + 1]) for i in range(0, len(rows) - 1, 2) if rows[i][0] == "buy" and rows[i + 1][0] == "sell"]
gross = net = 0.0
print("\nround trips (ETH, 1m):")
for b, s in pairs:
    g = s[4]; fee = 0.001 * (b[1] * b[2] + s[1] * s[2]); gross += g; net += g - fee
    print(f"  buy {b[2]:.2f} -> {s[3]:11s} {s[2]:.2f}   P&L {g:+8.2f}   after 0.1%/side fees {g - fee:+8.2f}   move {s[2] / b[2] - 1:+.2%}")
wins = sum(1 for b, s in pairs if s[4] > 0)
print(f"\n{len(pairs)} trades, {wins} wins; total {gross:+.2f} USD with zero fees, {net:+.2f} USD with 0.1%/side fees, on 100,000 paper capital")
