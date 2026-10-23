"""Research round 15: does the Kronos forecasting model predict crypto returns?

Kronos (github.com/shiyu-coder/Kronos, AAAI 2026) is an open-source
"foundation model" pre-trained on candles from 45+ exchanges. The
PkLavc/Autotrader repo the owner shared uses it to pick US stocks: forecast
the close 5 sessions ahead, buy the best forecasts above +1%.

Test here: Kronos-small, 400-day lookback, 3 samples (Autotrader's
settings), forecasting each coin's close 5 days ahead from every daily close
between 2025-09-01 and the end of the data. The model was published in
August 2025, so its training data cannot include this test period (the
earlier history may well have been in it, which is why nothing before
September 2025 is scored).

Measured:
  - information coefficient (IC): rank correlation, across the 15 coins on
    each day, between the forecast and the realised 5-day return
  - sign hit rate of the forecast
  - a portfolio: every 5 days hold the 3 best forecasts above +1% (equal
    weight, 0.15% cost per side), vs holding all 15 equally, vs BTC, vs the
    same rule with a naive forecast (last 5 days' return = next 5 days')

Requires torch, pandas, einops, huggingface_hub, safetensors and a clone of
the Kronos repo at KRONOS_DIR (default /home/user/shiyu-coder/kronos, commit
67b630e). Forecasts are cached in research/data/kronos_forecasts.pkl, so a
re-run only scores.
"""
import math
import os
import pickle
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..')))   # tradebot.data.Candle, for the pickles
KRONOS_DIR = os.environ.get('KRONOS_DIR', '/home/user/shiyu-coder/kronos')
COINS = "BTC ETH BNB XRP ADA DOGE SOL TRX LTC BCH LINK DOT AVAX NEAR UNI".split()
DAY = 86_400_000
H, LOOK, SAMPLES = 5, 400, 3

raw = pickle.load(open(os.path.join(DATA, 'daily_long.pkl'), 'rb'))
series = {c: raw[c + 'USDT'] for c in COINS}
idx = {c: {k.open_time: i for i, k in enumerate(cs)} for c, cs in series.items()}
from datetime import datetime, timezone
START = int(datetime(2025, 9, 1, tzinfo=timezone.utc).timestamp() * 1000)
END = min(cs[-1].open_time for cs in series.values()) - H * DAY   # need H days after to score
DATES = list(range(START, END + 1, DAY))
d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m-%d')

cache_path = os.path.join(DATA, 'kronos_forecasts.pkl')
fc = pickle.load(open(cache_path, 'rb')) if os.path.exists(cache_path) else {}
todo = [t for t in DATES if t not in fc]
if todo:
    sys.path.insert(0, KRONOS_DIR)
    import hashlib
    import numpy as np
    import pandas as pd
    import torch
    from model import Kronos, KronosPredictor, KronosTokenizer
    torch.set_num_threads(os.cpu_count())
    tok = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
    model = Kronos.from_pretrained("NeoQuasar/Kronos-small")
    pred = KronosPredictor(model, tok, device="cpu", max_context=512)
    t_start = time.time()
    for n, t in enumerate(todo):
        dfs, xs, ys = [], [], []
        for c in COINS:
            i = idx[c][t]
            cs = series[c][i - LOOK + 1:i + 1]
            dfs.append(pd.DataFrame([dict(open=k.open, high=k.high, low=k.low, close=k.close, volume=k.volume,
                                          amount=k.volume * k.close) for k in cs]))
            xs.append(pd.Series(pd.to_datetime([k.open_time for k in cs], unit='ms')))
            ys.append(pd.Series(pd.date_range(xs[-1].iloc[-1] + pd.Timedelta(days=1), periods=H, freq='D')))
        seed = int.from_bytes(hashlib.sha256(f"r15:{t}".encode()).digest()[:4], 'big')
        np.random.seed(seed); torch.manual_seed(seed)
        outs = pred.predict_batch(dfs, xs, ys, pred_len=H, T=1.0, top_p=0.9, sample_count=SAMPLES, verbose=False)
        fc[t] = {c: float(o['close'].iloc[-1]) / series[c][idx[c][t]].close - 1 for c, o in zip(COINS, outs)}
        if n % 10 == 0 or n == len(todo) - 1:
            pickle.dump(fc, open(cache_path, 'wb'))
            print(f"  forecast {d(t)} ({n + 1}/{len(todo)}, {time.time() - t_start:.0f}s)", flush=True)

# ---------- scoring ----------
def close(c, t):
    return series[c][idx[c][t]].close

def opn(c, t):
    return series[c][idx[c][t]].open

real = {t: {c: close(c, t + H * DAY) / close(c, t) - 1 for c in COINS} for t in DATES}
naive = {t: {c: close(c, t) / close(c, t - H * DAY) - 1 for c in COINS} for t in DATES}

def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v)
    for k, i in enumerate(o):
        r[i] = k
    return r

def corr(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / den if den else 0.0

def ic_stats(f):
    ics = [corr(rank([f[t][c] for c in COINS]), rank([real[t][c] for c in COINS])) for t in DATES]
    m = sum(ics) / len(ics); sd = math.sqrt(sum((x - m) ** 2 for x in ics) / len(ics))
    # forecasts overlap (5-day horizon, daily), so only every 5th day is independent
    n_ind = len(ics) / H
    hits = [(f[t][c] > 0) == (real[t][c] > 0) for t in DATES for c in COINS]
    return m, m / sd * math.sqrt(n_ind) if sd else 0, sum(hits) / len(hits), ics

def portfolio(f, top=3, floor=0.01, cost=0.0015, offset=0):
    eq, curve, held_days = 1.0, [], 0
    for t in DATES[offset::H]:
        picks = sorted((c for c in COINS if f is None or f[t][c] > floor), key=lambda c: -(f[t][c] if f else 0))
        picks = picks[:top] if f is not None else picks
        if picks:
            held_days += 1
            # decided at the close of t, bought at the next open, sold at the open H days later
            r = sum(opn(c, t + (H + 1) * DAY) / opn(c, t + DAY) - 1 for c in picks
                    if t + (H + 1) * DAY in idx[c]) / len(picks)
            eq *= (1 + r) * (1 - cost) ** 2
        curve.append(eq)
    peak, dd = 1.0, 0.0
    for e in curve:
        peak = max(peak, e); dd = min(dd, e / peak - 1)
    return eq - 1, dd, held_days, len(curve)

L = [f"Kronos-small, lookback {LOOK}, {SAMPLES} samples, horizon {H} days; {len(COINS)} coins; "
     f"scored {d(DATES[0])} -> {d(DATES[-1])} ({len(DATES)} daily forecast dates)\n"]
for name, f in (("Kronos", fc), ("naive (last 5d return)", naive)):
    m, tstat, hit, ics = ic_stats({t: f[t] for t in DATES})
    L.append(f"{name:24s} mean IC {m:+.3f}  t-stat {tstat:+.2f}  (days with positive IC: {sum(x > 0 for x in ics) / len(ics):.0%})  sign hit rate {hit:.1%}")
up = sum(real[t][c] > 0 for t in DATES for c in COINS) / (len(DATES) * len(COINS))
L.append(f"share of 5-day returns that were positive (hit rate of always saying 'up'): {up:.1%}")
avg_f = sum(fc[t][c] for t in DATES for c in COINS) / (len(DATES) * len(COINS))
avg_r = sum(real[t][c] for t in DATES for c in COINS) / (len(DATES) * len(COINS))
L.append(f"average forecast {avg_f:+.2%} vs average realised {avg_r:+.2%} per 5 days\n")

L.append("Portfolio every 5 days (top 3 forecasts above +1%, next-open to next-open, 0.15%/side), 5 start offsets:")
for name, f, kw in (("Kronos top 3 > +1%", fc, {}), ("Kronos top 3, no floor", fc, {"floor": -9}),
                    ("naive top 3 > +1%", naive, {}), ("all 15 equal weight", None, {"cost": 0.0})):
    res = [portfolio(f, offset=o, **kw) for o in range(H)]
    L.append(f"  {name:26s} total " + "  ".join(f"{r[0]:+6.1%}" for r in res) +
             f"   | worst DD {min(r[1] for r in res):6.1%}  invested {sum(r[2] for r in res) / sum(r[3] for r in res):.0%} of periods")
b0, b1 = close('BTC', DATES[0]), close('BTC', DATES[-1])
L.append(f"  BTC buy & hold over the scored window: {b1 / b0 - 1:+.1%}")
print("\n".join(L))
