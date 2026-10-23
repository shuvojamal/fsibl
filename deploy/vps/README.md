# Running the bot on your own VPS (Binance Spot testnet)

GitHub's servers are in the US, and Binance refuses API calls from there. A
VPS in a country Binance serves (Germany works) can reach it, and it has a
fixed IP address, so a Binance API key can be locked to it.

This setup trades the **Binance Spot testnet** (test money). It runs
alongside the OKX demo on GitHub; the app shows both (tap the account chip
at the top: **OKX** / **VPS**).

## What you need

- A Debian or Ubuntu VPS with root access.
- Binance testnet keys: https://testnet.binance.vision > log in with GitHub >
  *Generate HMAC_SHA256 Key*. The testnet account comes with test funds.

## Setup (about 5 minutes)

On the VPS, as root:

```bash
curl -fsSL -o setup.sh https://raw.githubusercontent.com/shuvojamal/binancebot/main/deploy/vps/setup.sh
# (the repo is private: if that download fails, copy deploy/vps/setup.sh over with scp)
bash setup.sh git@github.com:shuvojamal/binancebot.git
```

The script:

1. installs git and python3, and checks that this server can reach Binance;
2. creates a `tradebot` user with no login shell;
3. prints an SSH **deploy key**. Add it on GitHub under *repo > Settings >
   Deploy keys > Add deploy key*, tick **Allow write access**, and press
   Enter in the script. The key only opens this one repo.
4. clones the repo and runs the tests;
5. creates `/etc/tradebot.env` (readable only by root and the bot). Paste
   your testnet keys there: `nano /etc/tradebot.env`;
6. installs a systemd timer that runs `deploy/vps/run.sh` every 10 minutes.

First run now instead of waiting:

```bash
sudo -u tradebot touch /opt/tradebot/repo/binance_state/RUN_NOW
systemctl start tradebot
journalctl -u tradebot -f
```

## How it runs

- **Once a day, after the 00:00 UTC candle closes:** a full run, the same
  rules as the OKX demo (top 15 coins by volume, 5 of 8 checks, 1% risk,
  trailing stops, daily loss limit, circuit breaker, bad-data guard, fill
  tracking, self-audit).
- **Every 10 minutes:** it only checks whether the app left a request (Sell,
  Sell all, Run now, Reset breaker) and carries it out. Re-running on the
  same daily candle never trades twice.
- After each run it commits `binance_state/` and pushes, and the app shows it.
- Settings you change in the app (capital, risk, positions...) apply from
  the next run.
- The emergency backstop isn't available on Binance in this bot, so the
  setting is ignored there. The daily-close stop still applies.

## Everyday commands (on the VPS)

| | |
|---|---|
| Watch the log | `journalctl -u tradebot -f` |
| Stop the bot completely | `systemctl stop tradebot.timer` |
| Start it again | `systemctl start tradebot.timer` |
| Update the code | it pulls `main` before every run by itself |

## Notes

- The Binance testnet is reset from time to time: balances go back to the
  defaults and test orders disappear. If that happens, the bot logs that the
  exchange holds less than its records and follows the exchange.
- This setup never uses real money. The bot only trades a real account with
  `--live --i-accept-the-risk` and live keys, and that is a decision for the
  account owner to make, outside these scripts.
