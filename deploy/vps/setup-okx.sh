#!/usr/bin/env bash
# Move the OKX DEMO bot from GitHub Actions to this VPS (no Actions minutes).
# Run as root on the VPS, after setup.sh:      bash setup-okx.sh [/opt/tradebot]
#
# It creates (and changes nothing else):
#   <dir>/tradebot-okx.env       the OKX DEMO API key, secret and passphrase
#                                (root:tradebot, 640)
#   tradebot-okx.service/.timer  runs `run.sh okx` every 10 minutes, 2 minutes
#                                after the testnet timer: the daily run right
#                                after 00:00 UTC, plus the app's requests
#
# The OKX demo key: okx.com > Trade > Demo trading > (profile) Demo trading
# API > Create. Read + Trade only, no withdrawals. It's a demo key (test
# money); the bot uses OKX's demo trading header, never the real account.
set -euo pipefail
DIR="${1:-/opt/tradebot}"
ENV_FILE="$DIR/tradebot-okx.env"
[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }
[ -d "$DIR/repo/deploy/vps" ] || { echo "run setup.sh first ($DIR/repo not found)"; exit 1; }
for unit in tradebot-okx.service tradebot-okx.timer; do
  if [ -f "/etc/systemd/system/$unit" ] && ! grep -q "deploy/vps/run.sh" "/etc/systemd/system/$unit"; then
    echo "/etc/systemd/system/$unit already exists and isn't ours; stopping"; exit 1
  fi
done

printf '  %-40s ' "https://www.okx.com reachable?"
if curl -fsS -m 15 https://www.okx.com/api/v5/public/time | grep -q '"ts"'; then echo OK; else echo "NO: OKX is blocked from this server"; exit 1; fi

if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<'KEYS'
# OKX DEMO trading keys (test money). Read + Trade, no withdrawals.
OKX_API_KEY=
OKX_API_SECRET=
OKX_PASSPHRASE=
KEYS
fi
chown root:tradebot "$ENV_FILE"
chmod 640 "$ENV_FILE"

cat > /etc/systemd/system/tradebot-okx.service <<UNIT
[Unit]
Description=Trading bot, one pass (OKX DEMO account) - $DIR
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=tradebot
Group=tradebot
EnvironmentFile=$ENV_FILE
ExecStart=$DIR/repo/deploy/vps/run.sh okx
TimeoutStartSec=15min
Nice=10
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=$DIR
PrivateTmp=yes
ProtectHome=yes
UNIT
cat > /etc/systemd/system/tradebot-okx.timer <<'UNIT'
[Unit]
Description=OKX demo bot check every 10 minutes (offset from the testnet bot)

[Timer]
OnCalendar=*:2/10
Persistent=true
RandomizedDelaySec=30

[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload
systemctl enable --now tradebot-okx.timer

echo
echo "Done. Next:"
echo "  1. nano $ENV_FILE   and paste the OKX DEMO key, secret and passphrase"
echo "  2. In the app, OKX account: Run now (or wait for 00:05 UTC)."
echo "  3. Watch it:  journalctl -u tradebot-okx -f"
