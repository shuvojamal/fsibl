#!/usr/bin/env bash
# One-time repair when the VPS bot has stopped reaching GitHub (the app shows no
# new runs) because git got stuck half-way through a sync. Keeps this machine's
# records (positions, trades, logs, including any written while stuck), takes
# settings/requests and code from GitHub, then pushes. Safe to run when nothing
# is wrong. Run as root:
#   cd /opt/tradebot/repo && git fetch -q origin main && git show origin/main:deploy/vps/unstick.sh | bash
set -u
DIR="${TRADEBOT_DIR:-/opt/tradebot}/repo"
cd "$DIR" || { echo "no checkout at $DIR"; exit 1; }
sudo -u tradebot bash -s <<'INNER'
set -u
APP="settings.json CLOSE RESET_HALT RUN_NOW PAUSED"
git fetch -q origin main || { echo "can't reach GitHub (network or deploy key)"; exit 1; }
echo "before: $(git status | head -1)"
BK=$(mktemp -d)
for S in binance_state binance_live; do [ -d "$S" ] && cp -a "$S" "$BK/"; done
git rebase --abort 2>/dev/null; git merge --abort 2>/dev/null
# put back this machine's records written since the last good sync (skip app files
# and anything holding conflict markers)
for S in binance_state binance_live; do
  [ -d "$BK/$S" ] || continue
  for f in "$BK/$S"/* "$BK/$S"/.last_daily; do
    [ -f "$f" ] || continue; b=$(basename "$f")
    case " $APP " in *" $b "*) continue ;; esac
    grep -q '^<<<<<<< \|^>>>>>>> ' "$f" && { echo "skipped damaged $S/$b"; continue; }
    cp -a "$f" "$S/$b"
  done
  git add -A "$S"; git diff --cached --quiet || git commit -q -m "vps-bot: records kept by unstick.sh"
done
rm -rf "$BK"
git show origin/main:deploy/vps/run.sh | sed -n '/^APP_FILES=/,/^}$/p;/^sync() {/,/^}$/p' > "${SF:=$(mktemp)}"
STATE=binance_state; . "$SF"; rm -f "$SF"
if sync && git push -q origin HEAD:main; then echo "repaired: synced and pushed; the app will show the VPS again"
else echo "still not synced; send this output to Claude"; fi
echo "after: $(git status | head -1); last commit: $(git log -1 --format='%h %s')"
INNER
