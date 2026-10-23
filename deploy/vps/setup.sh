#!/usr/bin/env bash
# One-time setup of the trading bot on a Debian/Ubuntu VPS, against the
# Binance Spot TESTNET (test money). Run as root:
#
#   curl -fsSLO https://raw.githubusercontent.com/OWNER/REPO/main/deploy/vps/setup.sh   (or copy it over)
#   bash setup.sh git@github.com:OWNER/REPO.git
#
# What it does:
#   1. installs git + python3 and checks that Binance answers from this server
#   2. creates a locked-down "tradebot" user (no login shell)
#   3. makes an SSH deploy key so the VPS can pull the code and push its state
#      (you add the key to the GitHub repo with write access; nothing else can
#      be reached with it)
#   4. creates /etc/tradebot.env for the Binance testnet keys (readable only by
#      root and the bot)
#   5. installs a systemd timer that runs deploy/vps/run.sh every 10 minutes;
#      run.sh trades once a day after the daily close, and in between only acts
#      on requests from the dashboard app (sell, reset breaker, run now)
set -euo pipefail

REPO="${1:?usage: bash setup.sh git@github.com:OWNER/REPO.git}"
HOME_DIR=/opt/tradebot
ENV_FILE=/etc/tradebot.env

[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }

echo "== 1. packages"
apt-get update -q
apt-get install -y -q git python3 ca-certificates curl openssh-client

echo "== 2. can this server reach Binance?"
for url in https://testnet.binance.vision/api/v3/time https://api.binance.com/api/v3/time https://data-api.binance.vision/api/v3/time; do
  printf '  %-48s ' "$url"
  if curl -fsS -m 15 "$url" | grep -q serverTime; then echo OK; else echo "BLOCKED or unreachable"; fi
done

echo "== 3. bot user"
id tradebot >/dev/null 2>&1 || useradd --system --create-home --home-dir "$HOME_DIR" --shell /usr/sbin/nologin tradebot
install -d -o tradebot -g tradebot -m 700 "$HOME_DIR/.ssh"

echo "== 4. deploy key"
if [ ! -f "$HOME_DIR/.ssh/id_ed25519" ]; then
  sudo -u tradebot ssh-keygen -q -t ed25519 -N "" -C "tradebot-vps" -f "$HOME_DIR/.ssh/id_ed25519"
fi
echo
echo "Add this public key to GitHub: repo > Settings > Deploy keys > Add deploy key,"
echo "title 'tradebot-vps', and TICK 'Allow write access' (the VPS pushes its state):"
echo
cat "$HOME_DIR/.ssh/id_ed25519.pub"
echo
read -r -p "Press Enter once the deploy key is added... "
sudo -u tradebot ssh -o StrictHostKeyChecking=accept-new -T git@github.com 2>&1 | grep -q "successfully authenticated" \
  || { echo "GitHub did not accept the key yet; add it and run this script again"; exit 1; }

echo "== 5. code"
if [ ! -d "$HOME_DIR/repo/.git" ]; then
  sudo -u tradebot git clone -q "$REPO" "$HOME_DIR/repo"
fi
sudo -u tradebot git -C "$HOME_DIR/repo" config user.name "tradebot-vps"
sudo -u tradebot git -C "$HOME_DIR/repo" config user.email "tradebot-vps@users.noreply.github.com"
sudo -u tradebot python3 -m unittest discover -s "$HOME_DIR/repo/tests" -t "$HOME_DIR/repo" >/dev/null 2>&1 \
  && echo "  tests pass" || echo "  WARNING: tests failed; check before trading"

echo "== 6. API keys"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<'KEYS'
# Binance Spot TESTNET keys (test money): https://testnet.binance.vision
# > log in with GitHub > Generate HMAC_SHA256 Key. Paste them below.
BINANCE_API_KEY=
BINANCE_API_SECRET=
KEYS
fi
chown root:tradebot "$ENV_FILE"
chmod 640 "$ENV_FILE"
echo "  edit $ENV_FILE and paste the testnet keys:  nano $ENV_FILE"

echo "== 7. timer"
install -m 644 "$HOME_DIR/repo/deploy/vps/tradebot.service" /etc/systemd/system/tradebot.service
install -m 644 "$HOME_DIR/repo/deploy/vps/tradebot.timer" /etc/systemd/system/tradebot.timer
systemctl daemon-reload
systemctl enable --now tradebot.timer

echo
echo "Done. Next:"
echo "  1. nano $ENV_FILE            # paste the Binance testnet keys"
echo "  2. sudo -u tradebot touch $HOME_DIR/repo/binance_state/RUN_NOW 2>/dev/null || true"
echo "     systemctl start tradebot   # first run now instead of waiting"
echo "  3. journalctl -u tradebot -f  # watch it"
echo "In the app, switch the account to 'Binance testnet (VPS)'."
