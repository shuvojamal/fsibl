# Review: three repos and the ai4trade skill (2026-10-23)

## martex-dev/martex-quant (MIT): the most useful thing shared so far

A one-person crypto research platform that is honest about its results.
It ran 174 pre-registered trials, killed most of them, and says so in its
README ("It is not a profitable trading bot"). Findings that bear on this
repo:

| Their finding | Ours | What we take |
|---|---|---|
| Funding carry: real, survives an honest universe, but **~0% in 2025–26** (H72) | Round 13: about +3%/yr on 2024–26, below stablecoin yield | Agrees. Keep the `funding` monitor; don't trade it now. |
| Cross-sectional rotation: validated in backtest, but ~40% of its Sharpe came from a hindsight universe (H71); live paper −17.5% in 7 weeks | Round 14: rejected, overfit and draws down deep | Agrees. Rotation stays rejected. |
| Picking the universe at the end of the sample inflates a ranking strategy's Sharpe ~40% | Our 55-coin pool is today's list (round 12 caveat) | Treat our backtest Sharpe as an upper bound; round 16 quantifies it. |
| Vol-target sizing "is the cure for drawdown" | Round 11 tested volatility-scaled risk and rejected it | No change; our ATR stop already sizes by volatility. |
| Funding extremes and spot–perp basis as contrarian signals: backwards (high funding → higher forward returns) | Not tested | Noted. Don't build contrarian funding signals. |
| Deflated Sharpe against all trials ever run | Not done before | **Done: round 16.** |
| Intraday (15m) families: all killed by costs | Rounds 0a/0b/5: same | Agrees. |

## PkLavc/Autotrader (MIT)

Reviewed separately in `docs/review-autotrader-2026-10-23.md`. We took its
state-audit idea: `tradebot audit`, run at the end of every daily workflow.
Its Kronos model is being tested in round 15.

## lisazhou886/Forex-hex-algo-strategy-mt4

The repo is a single README advertising a commercial MT4 "Expert Advisor".
It has no code, no backtest and no results. Nothing to test or use.

## Krexibd/quant-trading: MALWARE, do not open

It's a copy of the popular open-source `je-suis-tm/quant-trading`
collection with added files:

- A workflow commits a timestamp every minute so the repo looks active.
- A Visual Studio solution with a tiny C# project (`Form2`) sits inside a
  Python repo.
- The committed Visual Studio options file
  (`.vs/Trading-quant/v18/.suo`) contains a serialized .NET payload. When
  the solution is opened in Visual Studio on Windows, it runs
  `cmd /c powershell -WindowStyle Hidden …`, which repeatedly downloads a
  file from an outside site (`muckcoding.com`, with a raw.githubusercontent
  fallback) into `C:\Users\Public\Pictures`, decodes it with `certutil`,
  and runs it as a hidden PowerShell script with execution policy bypassed.
  That's a standard remote-access or info-stealer dropper.

Nothing from this repo was run. It was cloned once for reading only and
checked with `strings`. **If you opened it in Visual Studio on a Windows
PC**, treat that PC as compromised: disconnect it, scan it, and change
passwords and exchange API keys from a different, clean device.

## ai4trade.ai SKILL.md

A social copy-trading platform for AI agents. Agents register with email
and password, publish signals, follow other agents' signals, join paper
challenges for points, and are told to poll a "heartbeat" every 30–60 s.
Not registered: registration creates an outside account with the owner's
email and publishes under it, so it waits for the owner's explicit
go-ahead. On the merits, copying unverified signals from anonymous bots has
no evidence behind it. The only plausible use is publishing this bot's own
daily signals as a public track record.
