#!/usr/bin/env bash
# Called every 10 minutes by a systemd timer, as the "tradebot" user.
#
#   run.sh        Binance Spot TESTNET (test money), keys from tradebot.env,
#                 records in binance_state/          (tradebot.timer)
#   run.sh real   the owner's REAL Binance account, keys from tradebot-live.env,
#                 records in binance_live/           (tradebot-live.timer)
#
# The real account does nothing until the owner switches it on in the app:
# binance_live/settings.json "mode" = "test" (real keys, no orders: --dry-run)
# or "live" (real orders, only with the typed confirmation "I ACCEPT THE
# RISK"). Anything else, or no settings file, means off.
#
# It does a full run once a day after the 00:00 UTC candle closes, and in
# between only when the dashboard app left a request in binance_state/
# (CLOSE, RESET_HALT or RUN_NOW). Re-running on the same daily candle is
# safe: the bot never acts twice on one candle, it only carries out the
# request. State is committed and pushed so the app can show it.
set -euo pipefail

cd "$(dirname "$0")/../.."
# the test and real timers share one checkout: never run two passes at once
exec 9>"../.run.lock"
flock 9
MODE_ARG="${1:-test}"
if [ "$MODE_ARG" = real ]; then
  STATE=binance_live; DEFAULT_CAPITAL=300; VENUE="BINANCE REAL (VPS)"
else
  STATE=binance_state; DEFAULT_CAPITAL=5000; VENUE="BINANCE TESTNET (VPS)"
fi
mkdir -p "$STATE"

# Sync with GitHub without ever getting stuck. The app writes request files and
# settings into the state folder while this machine writes its records there, so
# the two can collide. On a conflict: this machine's records win, except files
# the app writes (settings, requests), where GitHub's copy wins; code always
# comes from GitHub. A rebase left half-done by an earlier pass is cleaned up.
APP_FILES="settings.json CLOSE RESET_HALT RUN_NOW PAUSED"
resolve() {   # finish a conflicted merge using the rules above
  git diff --name-only --diff-filter=U | while read -r f; do
    case "$f" in
      "$STATE"/*)
        base=${f#"$STATE"/}
        if echo " $APP_FILES " | grep -q " $base "; then pick=theirs; else pick=ours; fi ;;
      *) pick=theirs ;;
    esac
    if git cat-file -e ":$([ $pick = ours ] && echo 2 || echo 3):$f" 2>/dev/null; then
      git checkout --"$pick" -- "$f" && git add -- "$f"
    else
      git rm -q --cached -- "$f" 2>/dev/null; rm -f -- "$f"
    fi
  done
  git -c core.editor=true commit -q --no-edit
}
sync() {
  [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ] && { echo "cleaning up an unfinished rebase"; git rebase --abort || true; }
  [ -f .git/MERGE_HEAD ] && { git merge --abort || true; }
  git fetch -q origin main || { echo "git fetch failed; running on the local copy"; return 1; }
  git -c core.editor=true merge -q --no-edit origin/main 2>/dev/null || resolve || { echo "merge failed; local copy kept"; git merge --abort; return 1; }
}
git add -A "$STATE" && { git diff --cached --quiet || git commit -q -m "vps-bot: records left from an earlier pass"; }
sync || true

today=$(date -u +%F)
reason=""
if [ "$(cat "$STATE/.last_daily" 2>/dev/null || true)" != "$today" ] && [ "$(date -u +%H%M)" -ge 0005 ]; then
  reason=daily
fi
for f in CLOSE RESET_HALT RUN_NOW; do
  if [ -f "$STATE/$f" ] && [ -z "$reason" ]; then reason="request ($f)"; fi
done
[ -n "$reason" ] || exit 0

# settings and requests from the app, validated and clamped
python3 -m tradebot controls --state-dir "$STATE" --default-capital "$DEFAULT_CAPITAL" > /tmp/tradebot-ctl.txt
ARGS=$(sed -n 1p /tmp/tradebot-ctl.txt)
GOLD=""; [ "$(sed -n 2p /tmp/tradebot-ctl.txt)" = gold ] && GOLD=PAXGUSDT
MAX_OPEN=$(sed -n 3p /tmp/tradebot-ctl.txt | cut -d= -f2)
MODE=$(sed -n 4p /tmp/tradebot-ctl.txt | cut -d= -f2)
MIN_SCORE=$(sed -n 5p /tmp/tradebot-ctl.txt | cut -d= -f2)
IGNORE=$(sed -n 6p /tmp/tradebot-ctl.txt | cut -d= -f2)
REAL=""; REPORT_REAL=""
if [ "$MODE_ARG" = real ]; then
  case "$MODE" in
    test) REAL="--live --i-accept-the-risk --dry-run"; REPORT_REAL="--live" ;;
    live) REAL="--live --i-accept-the-risk"; REPORT_REAL="--live" ;;
    *) rm -f "$STATE/RUN_NOW" "$STATE/CLOSE" "$STATE/RESET_HALT"; exit 0 ;;   # off: do nothing at all
  esac
fi
[ -n "${BINANCE_API_KEY:-}" ] || { echo "BINANCE_API_KEY is empty: put the keys in the keys file in the install directory"; exit 1; }
echo "[$(date -u '+%F %T') UTC] run: $reason${REAL:+ (REAL ACCOUNT, mode $MODE)}" | tee -a "$STATE/run.log"

TOP=$(python3 -m tradebot scan --top 15 --symbols-only)
HELD=$(python3 -c '
import json, os
p = "'"$STATE"'/live_state.json"
if os.path.exists(p):
    print(" ".join(s for s, q in json.load(open(p)).get("positions", {}).items() if q.get("qty", 0) > 0))')
SYMS=$(echo $TOP $HELD $GOLD | tr ' ' '\n' | sort -u | tr '\n' ' ')

set +e
# shellcheck disable=SC2086  # ARGS and SYMS are validated word lists
python3 -u -m tradebot live $SYMS --exchange binance --strategy opportunity --interval 1d \
  $ARGS $REAL --no-adopt --state-dir "$STATE" --once 2>&1 | tee -a "$STATE/run.log"
ok=${PIPESTATUS[0]}
set -e
rm -f "$STATE/CLOSE" "$STATE/RESET_HALT" "$STATE/RUN_NOW"
if [ "$MODE_ARG" = real ] && [ "$ok" = 0 ]; then
  # "Sell all + Off" from the app: the sale has run, now switch the real account off
  python3 - "$STATE/settings.json" <<'PY'
import json, sys
p = sys.argv[1]
try:
    s = json.load(open(p))
except (OSError, ValueError):
    sys.exit(0)
if s.pop("stop_after_close", False):
    s["mode"] = "off"; s.pop("confirm", None)
    json.dump(s, open(p, "w"), indent=2)
    print("real account switched off after selling everything")
PY
fi
python3 -m tradebot report $SYMS --exchange binance $REPORT_REAL --state-dir "$STATE" > "$STATE/report.txt" 2>&1 || true
python3 -m tradebot shadow $SYMS --state-dir "$STATE" --max-open "$MAX_OPEN" --min-score "$MIN_SCORE" --ignore-check $IGNORE > "$STATE/shadow.txt" 2>&1 || true
python3 - <<PY
import json, datetime
from tradebot.control import read_controls
c = read_controls("$STATE", 5000)
for k in ("close", "reset_halt", "notes"):
    c.pop(k)
json.dump({"time": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
           "venue": "$VENUE", "reason": "$reason", "ok": $ok == 0,
           "symbols": "$SYMS".split(), **c}, open("$STATE/last_run.json", "w"), indent=2)
PY
if [ "$ok" = 0 ] && [ "$reason" = daily ]; then echo "$today" > "$STATE/.last_daily"; fi
python3 -m tradebot audit --state-dir "$STATE" --max-open "$MAX_OPEN" | tee -a "$STATE/run.log" || ok=1

git add -A "$STATE"
git diff --cached --quiet || git commit -q -m "vps-bot: $reason $(date -u +%F)"
for _ in 1 2 3; do sync && git push -q origin HEAD:main && break || sleep 5; done
exit "$ok"
