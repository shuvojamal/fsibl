"""Technical indicators computed over plain lists of floats."""


def ema(values, period):
    out = [None] * len(values)
    if len(values) < period:
        return out
    k = 2 / (period + 1)
    prev = sum(values[:period]) / period
    out[period - 1] = prev
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi(values, period=14):
    """Wilder's RSI."""
    out = [None] * len(values)
    if len(values) <= period:
        return out
    gains = losses = 0.0
    for i in range(1, period + 1):
        change = values[i] - values[i - 1]
        gains += max(change, 0)
        losses += max(-change, 0)
    avg_gain, avg_loss = gains / period, losses / period

    def value(g, l):
        return 100.0 if l == 0 else 100 - 100 / (1 + g / l)

    out[period] = value(avg_gain, avg_loss)
    for i in range(period + 1, len(values)):
        change = values[i] - values[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(change, 0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-change, 0)) / period
        out[i] = value(avg_gain, avg_loss)
    return out


def sma(values, period):
    out = [None] * len(values)
    total = 0.0
    for i, v in enumerate(values):
        total += v
        if i >= period:
            total -= values[i - period]
        if i >= period - 1:
            out[i] = total / period
    return out


def atr(highs, lows, closes, period=14):
    """Average true range (Wilder smoothing)."""
    out = [None] * len(closes)
    trs = []
    for i in range(len(closes)):
        if i == 0:
            trs.append(highs[0] - lows[0])
        else:
            trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]),
                           abs(lows[i] - closes[i - 1])))
        if i == period - 1:
            out[i] = sum(trs) / period
        elif i >= period:
            out[i] = (out[i - 1] * (period - 1) + trs[i]) / period
    return out


def macd(values, fast=12, slow=26, signal=9):
    """Return (macd line, signal line, histogram)."""
    f, s = ema(values, fast), ema(values, slow)
    line = [None if a is None or b is None else a - b for a, b in zip(f, s)]
    start = next((i for i, v in enumerate(line) if v is not None), len(line))
    sig_tail = ema(line[start:], signal)
    sig = [None] * start + sig_tail
    hist = [None if a is None or b is None else a - b for a, b in zip(line, sig)]
    return line, sig, hist


def rolling_max(values, period):
    out = [None] * len(values)
    for i in range(period - 1, len(values)):
        out[i] = max(values[i - period + 1:i + 1])
    return out
