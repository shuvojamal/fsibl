#!/usr/bin/env bash
# Called by tradebot.timer every 10 minutes, as the "tradebot" user, with the
# keys from tradebot.env. Trades the Binance Spot TESTNET (test money).
#
# It does a full run once a day after the 00:00 UTC candle closes, and in
# between only when the dashboard app left a request in binance_state/
# (CLOSE, RESET_HALT or RUN_NOW). Re-running on the same daily candle is
# safe: the bot never acts twice on one candle, it only carries out the
# request. State is committed and pushed so the app can show it.
set -euo pipefail

cd "$(dirname "$0")/../.."
STATE=binance_state
mkdir -p "$STATE"

git pull -q --rebase --autostash || echo "git pull failed; running on the local copy"

today=$(date -u +%F)
reason=""
if [ "$(cat "$STATE/.last_daily" 2>/dev/null || true)" != "$today" ] && [ "$(date -u +%H%M)" -ge 0005 ]; then
  reason=daily
fi
for f in CLOSE RESET_HALT RUN_NOW; do
  if [ -f "$STATE/$f" ] && [ -z "$reason" ]; then reason="request ($f)"; fi
done
[ -n "$reason" ] || exit 0
[ -n "${BINANCE_API_KEY:-}" ] || { echo "BINANCE_API_KEY is empty: put the testnet keys in tradebot.env in the install directory"; exit 1; }
echo "[$(date -u '+%F %T') UTC] run: $reason" | tee -a "$STATE/run.log"

# settings and requests from the app, validated and clamped
python3 -m tradebot controls --state-dir "$STATE" --default-capital 5000 > /tmp/tradebot-ctl.txt
ARGS=$(sed -n 1p /tmp/tradebot-ctl.txt)
GOLD=""; [ "$(sed -n 2p /tmp/tradebot-ctl.txt)" = gold ] && GOLD=PAXGUSDT
MAX_OPEN=$(sed -n 3p /tmp/tradebot-ctl.txt | cut -d= -f2)

TOP=$(python3 -m tradebot scan --top 15 --symbols-only)
HELD=$(python3 -c '
import json, os
p = "binance_state/live_state.json"
if os.path.exists(p):
    print(" ".join(s for s, q in json.load(open(p)).get("positions", {}).items() if q.get("qty", 0) > 0))')
SYMS=$(echo $TOP $HELD $GOLD | tr ' ' '\n' | sort -u | tr '\n' ' ')

set +e
# shellcheck disable=SC2086  # ARGS and SYMS are validated word lists
python3 -u -m tradebot live $SYMS --exchange binance --strategy opportunity --interval 1d \
  $ARGS --no-adopt --state-dir "$STATE" --once 2>&1 | tee -a "$STATE/run.log"
ok=${PIPESTATUS[0]}
set -e
rm -f "$STATE/CLOSE" "$STATE/RESET_HALT" "$STATE/RUN_NOW"
python3 -m tradebot report $SYMS --exchange binance --state-dir "$STATE" > "$STATE/report.txt" 2>&1 || true
python3 - <<PY
import json, datetime
from tradebot.control import read_controls
c = read_controls("$STATE", 5000)
for k in ("close", "reset_halt", "notes"):
    c.pop(k)
json.dump({"time": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
           "venue": "BINANCE TESTNET (VPS)", "reason": "$reason", "ok": $ok == 0,
           "symbols": "$SYMS".split(), **c}, open("$STATE/last_run.json", "w"), indent=2)
PY
if [ "$ok" = 0 ] && [ "$reason" = daily ]; then echo "$today" > "$STATE/.last_daily"; fi
python3 -m tradebot audit --state-dir "$STATE" --max-open "$MAX_OPEN" | tee -a "$STATE/run.log" || ok=1

git add -A "$STATE"
git diff --cached --quiet || git commit -q -m "vps-bot: $reason $(date -u +%F)"
for _ in 1 2 3; do git pull -q --rebase && git push -q && break || sleep 5; done
exit "$ok"
