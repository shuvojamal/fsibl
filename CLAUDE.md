# Notes for Claude

- Save every piece of research to the repo, not just the conclusion:
  the script in `research/scripts/`, its raw output in `research/results/`,
  any new cached data in `research/data/`, a write-up in `docs/`, and a row
  in `research/README.md` (with the commit the code was at). Commit and push
  after each round. The owner asked for this explicitly.
- Run the tests before every commit: `python -m unittest discover -s tests -t .`
- Real-money trading needs `--live --i-accept-the-risk`; never add those
  flags on your own. Demo trading uses the OKX demo or Binance testnet.
