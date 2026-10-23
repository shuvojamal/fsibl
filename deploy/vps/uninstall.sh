#!/usr/bin/env bash
# Remove the trading bot from the VPS: the timer, the two systemd units, the
# bot user and its directory. Touches nothing else.
#   bash uninstall.sh [/opt/tradebot]
set -euo pipefail
DIR="${1:-/opt/tradebot}"
[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }
[ -d "$DIR/repo/deploy/vps" ] || { echo "$DIR doesn't look like the bot's directory; nothing removed"; exit 1; }
read -r -p "Remove the bot, its keys file and everything in $DIR? Type yes: " ok
[ "$ok" = yes ] || { echo "cancelled"; exit 0; }
systemctl disable --now tradebot.timer tradebot-live.timer 2>/dev/null || true
rm -f /etc/systemd/system/tradebot.service /etc/systemd/system/tradebot.timer \
      /etc/systemd/system/tradebot-live.service /etc/systemd/system/tradebot-live.timer
systemctl daemon-reload
rm -rf --one-file-system "$DIR"
id tradebot >/dev/null 2>&1 && userdel tradebot || true
echo "Removed. Also delete the 'tradebot-vps' deploy key on GitHub (repo > Settings > Deploy keys)."
