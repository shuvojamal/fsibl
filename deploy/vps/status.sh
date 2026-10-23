#!/usr/bin/env bash
# Quick health check of the bot on this VPS.   bash status.sh [/opt/tradebot]
DIR="${1:-/opt/tradebot}"
echo "== timers";       systemctl list-timers 'tradebot*' --no-pager | sed -n '1,3p'
echo "== real account"; cat "$DIR/repo/binance_live/last_run.json" 2>/dev/null | grep -E '"(time|mode|capital)"' || echo "off or not installed"
echo "== last run";     systemctl status tradebot.service --no-pager -n 0 | sed -n 1,4p
echo "== last result";  cat "$DIR/repo/binance_state/last_run.json" 2>/dev/null | head -12 || echo "no run yet"
echo "== positions";    sed -n '/open positions/,/unrealised/p' "$DIR/repo/binance_state/report.txt" 2>/dev/null || echo "no report yet"
echo "== recent log";   tail -n 15 "$DIR/repo/binance_state/run.log" 2>/dev/null || echo "no log yet"
