#!/usr/bin/env bash
# OPT-IN: add the owner's REAL Binance account next to the testnet bot.
# Run as root on the VPS, after setup.sh:      bash setup-live.sh [/opt/tradebot]
#
# It creates (and changes nothing else):
#   <dir>/tradebot-live.env     the REAL API key and secret (root:tradebot, 640)
#   tradebot-live.service/.timer  runs `run.sh real` every 10 minutes, 5 minutes
#                                 after the testnet timer
#
# Nothing trades until the owner switches the real account on in the app:
#   Off (default)  -> the timer does nothing
#   No-orders test -> reads the real balance and shows what it would buy (--dry-run)
#   Live           -> real orders; needs the typed confirmation "I ACCEPT THE RISK"
#
# Before creating the key on binance.com (API Management):
#   - enable Spot trading ONLY; no withdrawals, no margin, no futures
#   - restrict it to this server's IP address
set -euo pipefail
DIR="${1:-/opt/tradebot}"
ENV_FILE="$DIR/tradebot-live.env"
[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }
[ -d "$DIR/repo/deploy/vps" ] || { echo "run setup.sh first ($DIR/repo not found)"; exit 1; }
for unit in tradebot-live.service tradebot-live.timer; do
  if [ -f "/etc/systemd/system/$unit" ] && ! grep -q "deploy/vps/run.sh" "/etc/systemd/system/$unit"; then
    echo "/etc/systemd/system/$unit already exists and isn't ours; stopping"; exit 1
  fi
done

echo "This server's public IP (lock the Binance key to it): $(curl -fsS -m 10 https://api.ipify.org || echo unknown)"
printf '  %-40s ' "https://api.binance.com reachable?"
if curl -fsS -m 15 https://api.binance.com/api/v3/time | grep -q serverTime; then echo OK; else echo "NO: real Binance is blocked from this server"; exit 1; fi

if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<'KEYS'
# REAL Binance keys (real money). Spot trading only, no withdrawals,
# restricted to this server's IP. Never reuse the testnet keys here.
BINANCE_API_KEY=
BINANCE_API_SECRET=
KEYS
fi
chown root:tradebot "$ENV_FILE"
chmod 640 "$ENV_FILE"

cat > /etc/systemd/system/tradebot-live.service <<UNIT
[Unit]
Description=Trading bot, one pass (REAL Binance account; off until enabled in the app) - $DIR
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=tradebot
Group=tradebot
EnvironmentFile=$ENV_FILE
ExecStart=$DIR/repo/deploy/vps/run.sh real
TimeoutStartSec=15min
Nice=10
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=$DIR
PrivateTmp=yes
ProtectHome=yes
UNIT
cat > /etc/systemd/system/tradebot-live.timer <<'UNIT'
[Unit]
Description=Real-account bot check every 10 minutes (offset from the testnet bot)

[Timer]
OnCalendar=*:5/10
Persistent=true
RandomizedDelaySec=30

[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload
systemctl enable --now tradebot-live.timer

echo
echo "Done. The real account is installed and OFF. Next:"
echo "  1. nano $ENV_FILE        # paste the REAL key and secret"
echo "  2. In the app: account chip > 'Binance REAL (VPS)' > Bot tab > Real money: 'No-orders test'"
echo "  3. Within 10 minutes the app shows your real balance and what the bot would buy."
echo "  Only then, and only if it looks right: switch to 'Live' and type the confirmation."
