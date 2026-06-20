![PyPI](https://img.shields.io/pypi/v/lwcharts) ![license](https://img.shields.io/badge/license-MIT-green) ![python](https://img.shields.io/badge/python-3.10+-lightgrey)

# lwcharts

**TradingView-quality interactive charts from pandas data, in one fluent chain.**

```python
chart = (
    Chart("BTC/USDT — 1D", theme="dark", height=700)
    .candles(df)
    .line(ema_20, name="EMA 20", color="#f0b429")
    .line(ema_50, name="EMA 50", color="#a5b4fc", style="dashed")
    .volume(df)
    .add_subplot(
        Subplot(height_ratio=0.2, label="RSI(14)", y_min=0, y_max=100)
        .line(rsi, color="#58a6ff")
        .hline(70, style="dashed")
        .hline(30, style="dashed")
    )
    .markers(entries, shape="arrowUp", position="belowBar", color="#26a641", label="E")
)
chart.serve()
```

## Description

lwcharts is a simple python wrapper of the famous [TradingView's Lightweight Charts](https://www.tradingview.com/lightweight-charts/)

## Why lwcharts

- **Zero JS knowledge required.** You write pandas, you get interactive TradingView charts. Crosshair sync, scroll, zoom — all included.
- **Single `createChart` architecture.** All subpanes share one time axis. No manual sync hacks, no drift between panes.
- **No calculation, no opinion.** The lib renders what you give it. Your EMA, your RSI, your signals — computed with whatever tools you prefer.
- **Truly offline.** The lightweight-charts JS bundle is embedded in the generated HTML by default. Works on air-gapped machines, in Jupyter.
- **Zero dependencies beyond pandas.** No plotly, no bokeh, no nodejs, no webpack.

## Installation

```bash
uv add lwcharts
# or
pip install lwcharts
```

## Quickstart

```python
import numpy as np
import pandas as pd
from lwcharts import Chart, Subplot

rng = np.random.default_rng(42)
n = 300
idx = pd.date_range("2023-01-01", periods=n, freq="B")
close = 42000 + np.cumsum(rng.normal(0, 500, n))
df = pd.DataFrame({
    "open":   close - rng.uniform(0, 300, n),
    "high":   close + rng.uniform(0, 600, n),
    "low":    close - rng.uniform(0, 600, n),
    "close":  close,
    "volume": rng.integers(500_000_000, 2_000_000_000, n).astype(float),
}, index=idx)

ema_20 = df["close"].ewm(span=20).mean()
ema_50 = df["close"].ewm(span=50).mean()
delta  = df["close"].diff()
rsi    = 100 - 100 / (1 + delta.clip(lower=0).ewm(com=13).mean()
                            / (-delta.clip(upper=0)).ewm(com=13).mean())

entries = pd.Series(False, index=idx)
entries.iloc[[40, 120, 210]] = True

chart = (
    Chart("BTC/USDT — 1D", theme="dark", height=700)
    .candles(df)
    .line(ema_20, name="EMA 20", color="#f0b429")
    .line(ema_50, name="EMA 50", color="#a5b4fc", style="dashed")
    .volume(df)
    .add_subplot(
        Subplot(height_ratio=0.2, label="RSI(14)", y_min=0, y_max=100)
        .line(rsi, color="#58a6ff")
        .hline(70, style="dashed")
        .hline(30, style="dashed")
    )
    .markers(entries, shape="arrowUp", position="belowBar", color="#26a641", label="E")
)
chart.serve()        # opens browser at localhost:1337
chart.to_html("btc.html")   # or write a self-contained HTML file
```

## What the lib does not do

lwcharts is a rendering layer, not an analytics engine. It does not:

- Calculate indicators (EMA, RSI, MACD, Bollinger…)
- Fetch market data (no Bloomberg, CCXT, Yahoo Finance connectors)
- Resample OHLCV (1D → 1W resampling belongs in pandas)

**You keep full control of your data pipeline.** Use pandas-ta, ta-lib, numpy, or
your own in-house library to compute whatever you need, then pass the resulting
Series directly to `lwcharts`.

## Documentation

Full API reference, all methods, edge cases, and complete code examples:
[docs/DOCUMENTATION.md](docs/DOCUMENTATION.md)

## License

MIT
