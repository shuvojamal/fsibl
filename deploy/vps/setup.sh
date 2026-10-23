#!/usr/bin/env bash
# One-time setup of the trading bot on a Debian/Ubuntu VPS that already runs
# other sites and apps. Everything lives in ONE directory (default
# /opt/tradebot) owned by its own system user; the only files outside it are
# two systemd units named tradebot.service / tradebot.timer. No ports are
# opened, no web server is touched, nothing is upgraded.
#
#   bash setup.sh git@github.com:OWNER/REPO.git [/opt/tradebot]
#
# Trades the Binance Spot TESTNET (test money). Undo everything with
# uninstall.sh.
set -euo pipefail

REPO="${1:?usage: bash setup.sh git@github.com:OWNER/REPO.git [install dir]}"
DIR="${2:-/opt/tradebot}"
BOT_USER=tradebot
ENV_FILE="$DIR/tradebot.env"

[ "$(id -u)" = 0 ] || { echo "run as root (sudo bash setup.sh ...)"; exit 1; }
case "$DIR" in /*) ;; *) echo "install dir must be an absolute path"; exit 1 ;; esac
for unit in tradebot.service tradebot.timer; do
  if [ -f "/etc/systemd/system/$unit" ] && ! grep -q "deploy/vps/run.sh" "/etc/systemd/system/$unit"; then
    echo "/etc/systemd/system/$unit already exists and isn't ours; stopping so nothing is overwritten"; exit 1
  fi
done

echo "== 1. tools (only installed if missing; nothing is upgraded)"
missing=""
for cmd in git python3 curl ssh; do command -v "$cmd" >/dev/null || missing="$missing $cmd"; done
if [ -n "$missing" ]; then
  echo "  installing:$missing"
  apt-get update -q
  apt-get install -y -q --no-upgrade git python3 curl openssh-client ca-certificates
fi
python3 -c 'import sys; assert sys.version_info >= (3, 9), sys.version' \
  || { echo "python3 is older than 3.9; the bot needs 3.9+"; exit 1; }
echo "  python $(python3 -c 'import platform; print(platform.python_version())'), $(git --version)"

echo "== 2. can this server reach Binance?"
for url in https://testnet.binance.vision/api/v3/time https://data-api.binance.vision/api/v3/time https://api.binance.com/api/v3/time; do
  printf '  %-48s ' "$url"
  if curl -fsS -m 15 "$url" 2>/dev/null | grep -q serverTime; then echo OK; else echo "BLOCKED or unreachable"; fi
done

echo "== 3. bot user and directory ($DIR)"
id "$BOT_USER" >/dev/null 2>&1 || useradd --system --home-dir "$DIR" --shell /usr/sbin/nologin "$BOT_USER"
install -d -o "$BOT_USER" -g "$BOT_USER" -m 750 "$DIR"
install -d -o "$BOT_USER" -g "$BOT_USER" -m 700 "$DIR/.ssh"

echo "== 4. deploy key (opens only this one GitHub repo)"
if [ ! -f "$DIR/.ssh/id_ed25519" ]; then
  sudo -u "$BOT_USER" ssh-keygen -q -t ed25519 -N "" -C "tradebot-vps" -f "$DIR/.ssh/id_ed25519"
fi
# keep the bot's SSH settings inside its own directory
cat > "$DIR/.ssh/config" <<SSH
Host github.com
  IdentityFile $DIR/.ssh/id_ed25519
  IdentitiesOnly yes
  UserKnownHostsFile $DIR/.ssh/known_hosts
  StrictHostKeyChecking accept-new
SSH
chown "$BOT_USER:$BOT_USER" "$DIR/.ssh/config"; chmod 600 "$DIR/.ssh/config"
export GIT_SSH_COMMAND="ssh -F $DIR/.ssh/config"
# `ssh -T git@github.com` exits 1 even when the key works (GitHub gives no
# shell), so judge by its message, not its exit code (pipefail would fail it).
gh_says=$(sudo -u "$BOT_USER" ssh -F "$DIR/.ssh/config" -T git@github.com 2>&1 || true)
if ! printf '%s' "$gh_says" | grep -q "successfully authenticated"; then
  echo
  echo "Add this public key on GitHub: repo > Settings > Deploy keys > Add deploy key,"
  echo "title 'tradebot-vps', and TICK 'Allow write access' (the VPS pushes its results):"
  echo
  cat "$DIR/.ssh/id_ed25519.pub"
  echo
  read -r -p "Press Enter once the deploy key is added... "
  gh_says=$(sudo -u "$BOT_USER" ssh -F "$DIR/.ssh/config" -T git@github.com 2>&1 || true)
  printf '%s' "$gh_says" | grep -q "successfully authenticated" \
    || { echo "GitHub did not accept the key yet ($gh_says); add it and run this script again"; exit 1; }
fi
echo "  GitHub accepts the key"

echo "== 5. code"
if [ ! -d "$DIR/repo/.git" ]; then
  sudo -u "$BOT_USER" env GIT_SSH_COMMAND="$GIT_SSH_COMMAND" git clone -q "$REPO" "$DIR/repo"
fi
sudo -u "$BOT_USER" git -C "$DIR/repo" config user.name "tradebot-vps"
sudo -u "$BOT_USER" git -C "$DIR/repo" config user.email "tradebot-vps@users.noreply.github.com"
sudo -u "$BOT_USER" git -C "$DIR/repo" config core.sshCommand "ssh -F $DIR/.ssh/config"
if sudo -u "$BOT_USER" sh -c "cd '$DIR/repo' && python3 -m unittest discover -s tests -t . >/dev/null 2>&1"; then
  echo "  tests pass"
else
  echo "  WARNING: tests failed; check before trading"
fi

echo "== 6. API keys file ($ENV_FILE)"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<'KEYS'
# Binance Spot TESTNET keys (test money): https://testnet.binance.vision
# > log in with GitHub > Generate HMAC_SHA256 Key. Paste them below.
BINANCE_API_KEY=
BINANCE_API_SECRET=
KEYS
fi
chown "root:$BOT_USER" "$ENV_FILE"
chmod 640 "$ENV_FILE"

echo "== 7. systemd timer (every 10 minutes)"
cat > /etc/systemd/system/tradebot.service <<UNIT
[Unit]
Description=Trading bot, one pass (Binance Spot testnet) - $DIR
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$BOT_USER
Group=$BOT_USER
EnvironmentFile=$ENV_FILE
ExecStart=$DIR/repo/deploy/vps/run.sh
TimeoutStartSec=15min
Nice=10
# hardening: the bot can write only its own directory, and sees no other home
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=$DIR
PrivateTmp=yes
ProtectHome=yes
UNIT
install -m 644 "$DIR/repo/deploy/vps/tradebot.timer" /etc/systemd/system/tradebot.timer
systemctl daemon-reload
systemctl enable --now tradebot.timer

echo
echo "Done. Everything is in $DIR. Next:"
echo "  1. nano $ENV_FILE                                   # paste the Binance testnet keys"
echo "  2. sudo -u $BOT_USER mkdir -p $DIR/repo/binance_state && sudo -u $BOT_USER touch $DIR/repo/binance_state/RUN_NOW"
echo "     systemctl start tradebot                         # first run now"
echo "  3. journalctl -u tradebot -f                         # watch it"
echo "In the app, tap the account chip at the top and pick 'Binance testnet (VPS)'."
