# lwcharts — Technical Reference

## Table of contents

1. [Installation & configuration](#1-installation--configuration)
2. [Key concepts](#2-key-concepts)
3. [Chart — full reference](#3-chart--full-reference)
4. [Subplot — full reference](#4-subplot--full-reference)
5. [Dashboard — full reference](#5-dashboard--full-reference)
6. [Data conventions and edge cases](#6-data-conventions-and-edge-cases)
7. [Complete usage examples](#7-complete-usage-examples)
8. [Styles and themes](#8-styles-and-themes)
9. [Offline mode and packaging](#9-offline-mode-and-packaging)

---

## 1. Installation & configuration

```bash
uv add lwcharts
# or
pip install lwcharts
```

**Requirements:** Python 3.10+, pandas ≥ 1.5. No other runtime dependency.

### offline parameter

Every `Chart` and `Dashboard` accepts an `offline` parameter (default `True`).

| Value | Behaviour | HTML size |
|---|---|---|
| `True` (default) | Vendor JS (~192 KB) inlined in the HTML | ~200 KB |
| `False` | `<script src="https://unpkg.com/...">` tag | ~2 KB |

Use `offline=True` (the default) whenever the rendered HTML may be opened in an
environment without internet access: corporate networks with SSL inspection, VPN,
air-gapped servers, Jupyter running locally, HTML reports shared by email.

```python
Chart("title", offline=True)   # default — fully self-contained
Chart("title", offline=False)  # CDN — requires internet at render time
```

---

## 2. Key concepts

### Rendering pipeline

```
Python (Chart / Subplot objects)
    → _build_config() → JSON dict
    → injected into chart.html template as __CHART_CONFIG__
    → browser runs lightweight-charts v5 JS
    → interactive canvas
```

The only Python→JS interface is the JSON config. No server is needed for Jupyter
rendering (`_repr_html_` returns a base64 data-URI iframe).

### Chart

The main object. Holds a primary pane (pane 0) that can contain candlestick data,
overlay series (lines, areas, histograms), horizontal price lines, markers, and
background zone highlights. `.candles()` is optional — if omitted, pane 0 is
driven by the first overlay series added.

### Subplot

A secondary pane stacked below the primary pane. Each `Subplot` becomes pane 1,
2, 3… in the JS `createChart` call, in the order they were added via
`.add_subplot()`. All panes share the same time axis: scrolling, zooming, and
crosshair movement are synchronised automatically by lightweight-charts v5.

### Dashboard

A CSS grid of independent Charts. Each cell has its own `createChart()` instance;
panes within a cell are synchronised, but cells are not synchronised with each
other.

---

## 3. Chart — full reference

### `Chart(title, theme, height, candle_style, offline, y_format)`

```python
Chart(
    title: str = "",
    theme: str = "dark",          # "dark" | "light"
    height: int = 600,            # total height in px
    candle_style: str = "classic",# "classic" | "hollow" | "bars"
    offline: bool = True,
    y_format: str | None = None,  # Y axis format for main pane; see section 8
)
```

All methods return `self` to allow chaining.

---

### `.candles(df, open, high, low, close, time)`

Adds OHLCV candlestick data to pane 0. Optional — omit for line/area-only charts.

```python
.candles(
    df: pd.DataFrame,
    open:  str | None = None,  # column name; auto-detected if None
    high:  str | None = None,
    low:   str | None = None,
    close: str | None = None,
    time:  str | None = None,  # column name; None = use DataFrame index
)
```

**Auto-detection:** columns named `open/high/low/close` or `o/h/l/c`
(case-insensitive) are detected automatically. Explicit names override detection.

**Index formats accepted:** `DatetimeIndex`, ISO date strings (`"2024-01-02"`),
unix timestamps (int or float seconds). Intraday data (time ≠ 00:00:00) is
serialised as unix int; daily data as `"YYYY-MM-DD"` strings.

```python
chart.candles(df)                          # auto-detect columns, use index as time
chart.candles(df, open="o", high="h", low="l", close="c")
chart.candles(df, time="timestamp")        # time stored in a column
```

---

### `.line(series, col, name, color, width, style, fill_method)`

Adds a line series to pane 0 as an overlay.

```python
.line(
    series: pd.Series | pd.DataFrame,
    col:    str | None = None,     # required if series is a DataFrame
    name:   str | None = None,
    color:  str | None = None,     # CSS color; auto-assigned from palette if None
    width:  int = 1,               # 1–4
    style:  str = "solid",         # "solid"|"dashed"|"dotted"|"large_dashed"|"sparse_dotted"
    fill_method: str | None = "ffill",
)
```

**fill_method** controls how the series is aligned to the candle index when their
indices differ. See [section 6](#6-data-conventions-and-edge-cases) for details.

```python
chart.line(ema_20, name="EMA 20", color="#f0b429", width=1)
chart.line(ema_50, name="EMA 50", color="#a5b4fc", style="dashed")

# partial line — visible only for the given index range
resistance = pd.Series(52000.0, index=pd.date_range("2024-03-01", "2024-03-10", freq="B"))
chart.line(resistance, color="#f85149", style="dashed", fill_method=None)
```

---

### `.area(series, col, name, top_color, bottom_color, line_color, fill_method)`

Adds a filled area series to pane 0.

```python
.area(
    series: pd.Series | pd.DataFrame,
    col:         str | None = None,
    name:        str | None = None,
    top_color:   str | None = None,   # fill color above the line
    bottom_color:str | None = None,   # fill color below the line
    line_color:  str | None = None,
    fill_method: str | None = "ffill",
)
```

```python
chart.area(
    equity,
    top_color="rgba(88,166,255,0.2)",
    bottom_color="rgba(88,166,255,0.0)",
    line_color="#58a6ff",
)
```

---

### `.baseline(series, col, name, base, fill_method)`

Adds a baseline series: values above `base` are rendered with one color scheme,
values below with another. Useful for P&L, excess return, spread vs mean.

```python
.baseline(
    series: pd.Series | pd.DataFrame,
    col:    str | None = None,
    name:   str | None = None,
    base:   float = 0.0,
    top_line_color:    str = "rgba(38,166,154,1)",
    top_fill_color1:   str = "rgba(38,166,154,0.28)",
    top_fill_color2:   str = "rgba(38,166,154,0.05)",
    bottom_line_color: str = "rgba(239,83,80,1)",
    bottom_fill_color1:str = "rgba(239,83,80,0.05)",
    bottom_fill_color2:str = "rgba(239,83,80,0.28)",
    fill_method: str | None = "ffill",
)
```

```python
chart.baseline(excess_return, base=0.0, name="Excess Return vs Benchmark")
```

---

### `.histogram(series, col, name, color, color_up, color_down, fill_method)`

Adds a histogram (bar chart) series to pane 0.

```python
.histogram(
    series: pd.Series | pd.DataFrame,
    col:        str | None = None,
    name:       str | None = None,
    color:      str | None = None,       # uniform color for all bars
    color_up:   str | None = None,       # color when value > 0
    color_down: str | None = None,       # color when value < 0
    fill_method:str | None = "ffill",
)
```

If `color_up` and `color_down` are provided, per-bar colors are computed in
Python before serialisation. `color` is used only when `color_up`/`color_down`
are absent.

```python
chart.histogram(volume, color="rgba(88,166,255,0.4)")
chart.histogram(macd_hist, color_up="#26a641", color_down="#f85149")
```

---

### `.volume(df, col, position, up_color, down_color)`

Convenience method for OHLCV volume. Handles per-bar up/down color automatically.

```python
.volume(
    df:         pd.DataFrame,
    col:        str = "volume",
    time:       str | None = None,
    position:   str = "pane",                    # "pane" | "overlay"
    up_color:   str = "rgba(38,166,154,0.5)",
    down_color: str = "rgba(239,83,80,0.5)",
)
```

| position | Behaviour |
|---|---|
| `"pane"` (default) | Dedicated subplot inserted immediately below pane 0 |
| `"overlay"` | Histogram in pane 0, `priceScaleId: "volume"`, occupies bottom 25% |

```python
chart.volume(df)                        # subplot (default)
chart.volume(df, position="overlay")    # overlay in main pane
```

---

### `.hline(price, color, style, width, label)`

Adds an infinite horizontal price line to pane 0.

```python
.hline(
    price:  float,
    color:  str | None = None,     # default: "rgba(139,148,158,0.5)"
    style:  str = "dashed",
    width:  int = 1,
    label:  str | None = None,     # displayed on the Y axis
)
```

```python
chart.hline(50000, color="rgba(240,180,41,0.5)", label="ATH")
chart.hline(40000, style="solid", color="rgba(38,166,154,0.4)", label="Support")
```

---

### `.marker(time, shape, position, color, label)`

Adds a single marker symbol on the candle series.

```python
.marker(
    time:     str | pd.Timestamp | int,
    shape:    str = "circle",      # "arrowUp"|"arrowDown"|"circle"|"square"
    position: str = "aboveBar",    # "aboveBar"|"belowBar"|"inBar"
    color:    str | None = None,
    label:    str | None = None,   # short text displayed next to the symbol
)
```

```python
chart.marker("2024-03-15", shape="arrowUp", position="belowBar", color="#26a641", label="E")
```

---

### `.markers(items, shape, position, color, label)`

Batch version of `.marker()`. Accepts three input formats.

```python
.markers(
    items: list[dict] | pd.DataFrame | pd.Series,
    # keyword args below apply only when items is a pd.Series[bool]
    shape:    str = "circle",
    position: str = "aboveBar",
    color:    str | None = None,
    label:    str | None = None,
)
```

**Format 1 — list of dicts:** each dict must have keys `time`, `shape`,
`position`, `color`, `label`.

**Format 2 — pd.DataFrame:** same columns as the dict keys above.

**Format 3 — pd.Series[bool]:** a marker is placed at every `True` index value
using the `shape`, `position`, `color`, `label` keyword arguments.

```python
# list of dicts
chart.markers([
    {"time": "2024-01-10", "shape": "arrowUp",   "position": "belowBar", "color": "#26a641", "label": "E"},
    {"time": "2024-04-20", "shape": "arrowDown", "position": "aboveBar", "color": "#f85149", "label": "X"},
])

# boolean Series — entry signals
chart.markers(entries_mask, shape="arrowUp",   position="belowBar", color="#26a641", label="E")
chart.markers(exits_mask,   shape="arrowDown", position="aboveBar", color="#f85149", label="X")
```

---

### `.candle_colors(colors, color, apply_to)`

Overrides candle colors on a per-bar basis. Requires `.candles()` to have been
called first.

```python
.candle_colors(
    colors:   pd.Series,             # Series[str] (CSS colors) or Series[bool]
    color:    str | None = None,     # fixed color; used when colors is Series[bool]
    apply_to: str = "body",          # "body" | "wick" | "both"
)
```

**Series[str]:** each non-null value in the series overrides the candle color at
that timestamp. NaN → default up/down color.

**Series[bool]:** `True` rows get the `color` argument applied; `False` rows keep
the default.

```python
# highlight specific candles in orange
danger = pd.Series(index=df.index, dtype=object)
danger[volatility_mask] = "rgba(255,140,0,0.8)"
chart.candle_colors(danger)

# boolean shorthand
chart.candle_colors(df["close"] < sma_200, color="rgba(239,83,80,0.7)", apply_to="body")
```

---

### `.bg_zone(time_from, time_to, color)`

Adds a single background color band spanning a time range in pane 0.

```python
.bg_zone(
    time_from: str | pd.Timestamp | int,
    time_to:   str | pd.Timestamp | int,
    color:     str,
)
```

```python
chart.bg_zone("2024-03-01", "2024-03-31", "rgba(240,180,41,0.08)")
```

---

### `.bg_zones(items)`

Batch version of `.bg_zone()`.

```python
.bg_zones(
    items: list[dict] | pd.DataFrame,
    # each item/row must have keys: from, to, color
)
```

```python
chart.bg_zones([
    {"from": "2024-01-01", "to": "2024-02-01", "color": "rgba(38,166,154,0.08)"},
    {"from": "2024-04-01", "to": "2024-05-01", "color": "rgba(239,83,80,0.08)"},
])
```

---

### `.bg_zones_from_series(series, palette)`

Converts a categorical Series into background zones. Contiguous runs of the same
label are merged into a single zone rectangle.

```python
.bg_zones_from_series(
    series:  pd.Series,       # categorical / object dtype
    palette: dict[str, str],  # {label: CSS color}
)
```

Labels absent from `palette` are silently ignored. NaN values produce no zone.

```python
regime = pd.Series("neutral", index=df.index)
regime[ema_fast > ema_slow] = "bull"
regime[ema_fast < ema_slow] = "bear"

palette = {
    "bull":    "rgba(38,166,154,0.09)",
    "bear":    "rgba(239,83,80,0.07)",
    "neutral": "rgba(139,148,158,0.04)",
}
chart.bg_zones_from_series(regime, palette)
```

---

### `.bg_zones_from_mask(mask, color_true, color_false)`

Converts a boolean Series into background zones. Contiguous `True` runs become
one zone; contiguous `False` runs become another (if `color_false` is provided).

```python
.bg_zones_from_mask(
    mask:        pd.Series,           # bool dtype
    color_true:  str,
    color_false: str | None = None,   # omit to leave False periods uncolored
)
```

```python
chart.bg_zones_from_mask(
    pnl > 0,
    color_true="rgba(38,166,154,0.06)",
    color_false="rgba(239,83,80,0.06)",
)
```

---

### `.add_subplot(subplot)`

Appends a `Subplot` as the next pane below pane 0. Panes are numbered in
insertion order: first `.add_subplot()` call → pane 1, second → pane 2, etc.

```python
chart.add_subplot(Subplot(height_ratio=0.2, label="RSI(14)", y_min=0, y_max=100)
                  .line(rsi, color="#58a6ff"))
```

---

### Rendering methods

#### `.show()`

Writes a temporary HTML file and opens it in the default browser.

#### `.serve(port=1337, open_browser=True)`

Starts a blocking HTTP server on `localhost:port`. Press `Ctrl-C` to stop.
Raises `OSError` if the port is already in use.

```python
chart.serve()            # port 1337
chart.serve(port=8080)
```

#### `.to_html(path)`

Writes a self-contained HTML file to disk.

```python
chart.to_html("report.html")
chart.to_html(Path("outputs") / "btc_daily.html")
```

#### `._repr_html_()`

Returns the full HTML as a string wrapped in a `<iframe src="data:text/html;base64,...">`.
Called automatically by Jupyter/IPython when the chart object is the last
expression in a cell.

```python
# In Jupyter — just evaluate the chart:
chart   # displays inline
```

---

## 4. Subplot — full reference

### `Subplot(height_ratio, label, y_min, y_max, y_format)`

```python
Subplot(
    height_ratio: float = 0.2,    # fraction of Chart.height allocated to this pane
    label:        str | None = None,
    y_min:        float | None = None,   # fix Y axis minimum
    y_max:        float | None = None,   # fix Y axis maximum
    y_format:     str | None = None,     # Y axis format; see section 8
)
```

`height_ratio` is relative to the total chart height. If the sum of all subplot
ratios exceeds 1, the primary pane is clamped to a minimum of 35% of total height.

**`y_min` / `y_max` — all or nothing.** Both must be provided together, or both
must be `None`. If only one is set, a `UserWarning` is raised, both are ignored,
and the pane falls back to full autoscale. This prevents the degenerate case where
fixing only `y_max=0` on a drawdown pane causes lightweight-charts to produce an
unusable Y range.

```python
Subplot(height_ratio=0.2, label="RSI", y_min=0, y_max=100)   # OK — bounded
Subplot(height_ratio=0.3, label="Drawdown")                   # OK — full autoscale
Subplot(height_ratio=0.3, label="Drawdown", y_max=0)          # UserWarning → autoscale
```

`y_format` controls the Y axis tick format and crosshair tooltip for all series
in this pane. See [section 8 — Y axis formats](#y-axis-formats-y_format) for
available values.

---

### Series methods

All methods return `self`. Signatures are identical to their `Chart` counterparts
with the same parameters. Methods available on `Subplot`:

#### `.line(series, col, name, color, width, style, fill_method)`
#### `.area(series, col, name, top_color, bottom_color, line_color, fill_method)`
#### `.baseline(series, col, name, base, fill_method)`
#### `.histogram(series, col, name, color, color_up, color_down, fill_method)`

See the [Chart section](#3-chart--full-reference) for full parameter descriptions.
Behaviour is identical; the series is placed in this subplot's pane index.

#### `.candles(df, open, high, low, close, time, style, up_color, down_color)`

Available on `Subplot` only (not on the main Chart's overlay API). Adds OHLCV
candles as the primary series of this pane. Useful for multi-timeframe layouts
where a lower-frequency OHLCV series is shown in a dedicated subplot.

```python
.candles(
    df:        pd.DataFrame,
    open:      str | None = None,
    high:      str | None = None,
    low:       str | None = None,
    close:     str | None = None,
    time:      str | None = None,
    style:     str = "classic",          # "classic" | "hollow" | "bars"
    up_color:  str = "#26a641",
    down_color:str = "#f85149",
)
```

```python
Subplot(height_ratio=0.3, label="Weekly")
.candles(df_weekly, style="hollow")
.line(ema5w, color="#f0b429")
```

---

### `.hline(price, color, style, width, label)`

Identical to `Chart.hline()`. The price line is attached to the first series of
this subplot's pane.

---

### Background zone methods

Identical API to the `Chart` equivalents; zones are applied to this subplot's pane.

- `.bg_zone(time_from, time_to, color)`
- `.bg_zones(items)`
- `.bg_zones_from_series(series, palette)`
- `.bg_zones_from_mask(mask, color_true, color_false)`

---

## 5. Dashboard — full reference

### `Dashboard(title, cols, row_height, theme, offline)`

```python
Dashboard(
    title:      str = "",
    cols:       int = 2,
    row_height: int = 500,     # height in px applied to every Chart in the grid
    theme:      str = "dark",
    offline:    bool = True,
)
```

Each Chart added to the dashboard has its own `createChart()` JS instance.
Panes within a chart are synchronised; charts in different cells are independent.

---

### `.add(chart)`

Adds a `Chart` to the next cell in the grid (left to right, top to bottom).
Returns `self`.

```python
dash.add(chart_btc).add(chart_eth).add(chart_sol).add(chart_bnb)
```

---

### Rendering methods

#### `.serve(port=1338, open_browser=True)`

Starts a blocking HTTP server. Raises `OSError` on port conflict.

#### `.to_html(path)`

Writes a self-contained HTML file.

#### `._repr_html_()`

Returns a base64 iframe for Jupyter inline display.

---

## 6. Data conventions and edge cases

### Accepted time index formats

All three formats can be used as the DataFrame/Series index or as a `time` column:

| Format | Example | JS serialisation |
|---|---|---|
| `DatetimeIndex` at midnight | `2024-01-02 00:00:00` | `"2024-01-02"` |
| `DatetimeIndex` with time | `2024-01-02 09:30:00` | unix int (seconds) |
| ISO date string | `"2024-01-02"` | passed through as-is |
| Unix int / float | `1704153600` | int |

**Consistency rule:** all series in a chart should use the same time format. The
format is determined by the candle index when `.candles()` is called. Mixing
`"YYYY-MM-DD"` strings and unix ints in the same chart will cause misalignment in
the JS time scale.

---

### `fill_method`

Controls how a series is aligned to the candle index when their indices differ.

| Value | Behaviour |
|---|---|
| `"ffill"` (default) | Reindex on candle index, forward-fill gaps |
| `"bfill"` | Reindex on candle index, backward-fill gaps |
| `None` | No reindex; gaps appear as whitespace in the chart |

**Automatic warning:** if `fill_method="ffill"` is requested and the series covers
less than 50% of the candle index, a `UserWarning` is raised and `fill_method` is
silently set to `None`. This prevents a partial indicator (e.g. a 5-day signal)
from being forward-filled across hundreds of candles unintentionally. Pass
`fill_method="ffill"` explicitly to suppress the warning.

---

### Partial lines (temporary resistance, event windows)

To draw a line that spans only a subset of the time range, pass a Series with a
reduced index and `fill_method=None`. The line will appear only where the index
has values; the rest of the chart will show whitespace.

```python
resistance = pd.Series(52000.0, index=pd.date_range("2024-03-01", "2024-03-15", freq="B"))
chart.line(resistance, color="#f85149", style="dashed", width=2, fill_method=None)
```

---

### Low-frequency indicators on a high-frequency chart

For a weekly signal displayed on a daily chart, use `fill_method="ffill"`. The
value as of each weekly bar is repeated forward until the next weekly bar.

```python
weekly_signal = pd.Series(...)    # index = every Monday
chart.line(weekly_signal, name="Weekly signal", fill_method="ffill")
```

---

## 7. Complete usage examples

All examples use `np.random.default_rng(42)` for reproducibility. Copy-paste
ready; no external data required.

---

### Case 1 — Classical technical analysis

Candlesticks + EMA 20/50 + volume + RSI + MACD.

```python
import numpy as np
import pandas as pd
from lwcharts import Chart, Subplot

rng = np.random.default_rng(42)
n = 400
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

delta = df["close"].diff()
gain  = delta.clip(lower=0).ewm(com=13).mean()
loss  = (-delta.clip(upper=0)).ewm(com=13).mean()
rsi   = 100 - 100 / (1 + gain / loss)

ema_fast  = df["close"].ewm(span=12).mean()
ema_slow  = df["close"].ewm(span=26).mean()
macd_line = ema_fast - ema_slow
signal    = macd_line.ewm(span=9).mean()
macd_hist = macd_line - signal

chart = (
    Chart("BTC/USDT — Technical Analysis", theme="dark", height=900)
    .candles(df)
    .line(ema_20, name="EMA 20", color="#f0b429", width=1)
    .line(ema_50, name="EMA 50", color="#a5b4fc", width=1, style="dashed")
    .volume(df)
    .add_subplot(
        Subplot(height_ratio=0.18, label="RSI(14)", y_min=0, y_max=100)
        .line(rsi, color="#58a6ff", width=1)
        .hline(70, color="rgba(248,81,73,0.4)", style="dashed")
        .hline(30, color="rgba(38,166,154,0.4)", style="dashed")
    )
    .add_subplot(
        Subplot(height_ratio=0.20, label="MACD(12,26,9)")
        .histogram(macd_hist, color_up="#26a641", color_down="#f85149")
        .line(macd_line, name="MACD",   color="#58a6ff", width=1)
        .line(signal,    name="Signal", color="#f0b429", width=1, style="dashed")
        .hline(0, color="rgba(139,148,158,0.3)", style="solid")
    )
)
chart.serve()
```

---

### Case 2 — P&L and equity curve

Equity line + drawdown area subplot + gain/loss background zones.

```python
import numpy as np
import pandas as pd
from lwcharts import Chart, Subplot

rng = np.random.default_rng(42)
n = 500
idx = pd.date_range("2022-01-01", periods=n, freq="B")
returns = rng.normal(0.0005, 0.012, n)
equity  = pd.Series((1 + returns).cumprod() * 100_000, index=idx, name="Equity")
pnl     = equity / 100_000 - 1
drawdown = (equity / equity.cummax() - 1).rename("Drawdown")

chart = (
    Chart("Equity Curve", theme="dark", height=600)
    .line(equity, name="Equity", color="#58a6ff", width=2)
    .hline(100_000, color="rgba(139,148,158,0.3)", style="solid")
    .bg_zones_from_mask(
        pnl > 0,
        color_true="rgba(38,166,154,0.06)",
        color_false="rgba(239,83,80,0.06)",
    )
    .add_subplot(
        Subplot(height_ratio=0.28, label="Drawdown", y_format="percent")
        .area(
            drawdown,
            top_color="rgba(239,83,80,0.0)",
            bottom_color="rgba(239,83,80,0.4)",
            line_color="#f85149",
        )
        .hline(0, color="rgba(139,148,158,0.3)", style="solid")
    )
)
chart.serve()
```

---

### Case 3 — Market regimes

Candlesticks + 3-state background zones from a categorical Series + candle
color override for danger periods.

```python
import numpy as np
import pandas as pd
from lwcharts import Chart

rng = np.random.default_rng(42)
n = 400
idx = pd.date_range("2023-01-01", periods=n, freq="B")
close = 42000 + np.cumsum(rng.normal(0, 500, n))
df = pd.DataFrame({
    "open":  close - rng.uniform(0, 300, n),
    "high":  close + rng.uniform(0, 600, n),
    "low":   close - rng.uniform(0, 600, n),
    "close": close,
    "volume": rng.integers(500_000_000, 2_000_000_000, n).astype(float),
}, index=idx)

ema_20 = df["close"].ewm(span=20).mean()
ema_50 = df["close"].ewm(span=50).mean()

regime = pd.Series("neutral", index=idx)
regime[ema_20 > ema_50 * 1.005] = "bull"
regime[ema_20 < ema_50 * 0.995] = "bear"

palette = {
    "bull":    "rgba(38,166,154,0.09)",
    "bear":    "rgba(239,83,80,0.07)",
    "neutral": "rgba(139,148,158,0.04)",
}

vol_mask = df["close"].pct_change().rolling(10).std() > 0.018

chart = (
    Chart("BTC — Market Regimes", theme="dark", height=600)
    .candles(df)
    .line(ema_20, name="EMA 20", color="#f0b429", width=1)
    .line(ema_50, name="EMA 50", color="#a5b4fc", width=1, style="dashed")
    .bg_zones_from_series(regime, palette)
    .candle_colors(vol_mask, color="rgba(255,140,0,0.75)", apply_to="body")
)
chart.serve()
```

---

### Case 4 — Partial resistance and entry/exit signals

Temporary resistance line + entry/exit markers + permanent support hline.

```python
import numpy as np
import pandas as pd
from lwcharts import Chart

rng = np.random.default_rng(42)
n = 300
idx = pd.date_range("2023-01-01", periods=n, freq="B")
close = 42000 + np.cumsum(rng.normal(0, 500, n))
df = pd.DataFrame({
    "open":  close - rng.uniform(0, 300, n),
    "high":  close + rng.uniform(0, 600, n),
    "low":   close - rng.uniform(0, 600, n),
    "close": close,
    "volume": rng.integers(500_000_000, 2_000_000_000, n).astype(float),
}, index=idx)

# partial resistance: only visible between day 80 and 100
resistance = pd.Series(
    df["close"].iloc[80:101].max() * 1.01,
    index=idx[80:101],
    name="Resistance",
)

entries = pd.Series(False, index=idx)
entries.iloc[[30, 110, 200]] = True
exits = pd.Series(False, index=idx)
exits.iloc[[60, 145, 250]] = True

chart = (
    Chart("BTC — Signals", theme="dark", height=600)
    .candles(df)
    .line(resistance, color="#f85149", style="dashed", width=2, fill_method=None)
    .hline(df["close"].min() * 0.99, color="rgba(38,166,154,0.4)", style="dashed", label="Support")
    .markers(entries, shape="arrowUp",   position="belowBar", color="#26a641", label="E")
    .markers(exits,   shape="arrowDown", position="aboveBar", color="#f85149", label="X")
)
chart.serve()
```

---

### Case 5 — Standalone chart without candles

Line + baseline + oscillator subplot; no OHLCV data required.

```python
import numpy as np
import pandas as pd
from lwcharts import Chart, Subplot

rng = np.random.default_rng(42)
n = 500
idx = pd.date_range("2022-01-01", periods=n, freq="B")
returns = rng.normal(0.0005, 0.012, n)
pnl     = pd.Series((1 + returns).cumprod() - 1, index=idx, name="P&L")
excess  = pnl - pd.Series((1 + rng.normal(0.0003, 0.009, n)).cumprod() - 1, index=idx)

# simple z-score oscillator
zscore = ((pnl - pnl.rolling(60).mean()) / pnl.rolling(60).std()).rename("Z-score")

chart = (
    Chart("Strategy — P&L standalone", theme="dark", height=550)
    .baseline(pnl, base=0.0, name="Cumulative P&L")
    .hline(0, color="rgba(139,148,158,0.3)", style="solid")
    .add_subplot(
        Subplot(height_ratio=0.28, label="60-day Z-score", y_min=-3, y_max=3)
        .line(zscore, color="#c084fc", width=1)
        .hline( 2, color="rgba(248,81,73,0.4)",   style="dashed", label="+2σ")
        .hline(-2, color="rgba(38,166,154,0.4)",  style="dashed", label="-2σ")
        .hline( 0, color="rgba(139,148,158,0.3)", style="dotted")
    )
)
chart.serve()
```

---

### Case 6 — Multi-timeframe

Daily candlesticks in pane 0 with regime zones; weekly candlesticks in a subplot.

```python
import numpy as np
import pandas as pd
from lwcharts import Chart, Subplot

rng = np.random.default_rng(42)
n = 500
idx_d = pd.date_range("2022-01-01", periods=n, freq="B")
close_d = 42000 + np.cumsum(rng.normal(0, 500, n))
df_daily = pd.DataFrame({
    "open":   close_d - rng.uniform(0, 300, n),
    "high":   close_d + rng.uniform(0, 600, n),
    "low":    close_d - rng.uniform(0, 600, n),
    "close":  close_d,
    "volume": rng.integers(500_000_000, 2_000_000_000, n).astype(float),
}, index=idx_d)

df_weekly = df_daily.resample("W-MON").agg(
    {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
).dropna()

ema_20d = df_daily["close"].ewm(span=20).mean()
ema5w   = df_weekly["close"].ewm(span=5).mean()
ema13w  = df_weekly["close"].ewm(span=13).mean()

regime_w = pd.Series("neutral", index=df_weekly.index)
regime_w[ema5w > ema13w] = "bull"
regime_w[ema5w < ema13w] = "bear"
regime_d = regime_w.reindex(df_daily.index, method="ffill").fillna("neutral")

palette = {
    "bull":    "rgba(38,166,154,0.09)",
    "bear":    "rgba(239,83,80,0.07)",
    "neutral": "rgba(139,148,158,0.04)",
}

chart = (
    Chart("Daily + Weekly — Multi-Timeframe", theme="dark", height=800)
    .candles(df_daily)
    .line(ema_20d, name="EMA 20D", color="#f0b429", width=1)
    .bg_zones_from_series(regime_d, palette)
    .add_subplot(
        Subplot(height_ratio=0.30, label="Weekly")
        .candles(df_weekly, style="hollow")
        .line(ema5w,  name="EMA 5W",  color="#f0b429", width=1)
        .line(ema13w, name="EMA 13W", color="#a5b4fc", width=1, style="dashed")
        .bg_zones_from_series(regime_w, palette)
    )
)
chart.serve()
```

---

### Case 7 — Multi-asset dashboard

2×2 grid, each cell a chart with candles + EMA + RSI. Written to a static HTML
file.

```python
import numpy as np
import pandas as pd
from lwcharts import Chart, Subplot, Dashboard

rng = np.random.default_rng(42)

def synthetic(start_price, n=300):
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    close = start_price + np.cumsum(rng.normal(0, start_price * 0.012, n))
    df = pd.DataFrame({
        "open":   close - rng.uniform(0, start_price * 0.007, n),
        "high":   close + rng.uniform(0, start_price * 0.015, n),
        "low":    close - rng.uniform(0, start_price * 0.015, n),
        "close":  close,
        "volume": rng.integers(500_000_000, 2_000_000_000, n).astype(float),
    }, index=idx)
    ema = df["close"].ewm(span=20).mean()
    delta = df["close"].diff()
    rsi = 100 - 100 / (1 + delta.clip(lower=0).ewm(com=13).mean()
                             / (-delta.clip(upper=0)).ewm(com=13).mean())
    return df, ema, rsi

assets = [("BTC/USDT", 42000), ("ETH/USDT", 2800), ("SOL/USDT", 100), ("BNB/USDT", 320)]

def make_chart(title, start_price):
    df, ema, rsi = synthetic(start_price)
    return (
        Chart(title, theme="dark", height=420)
        .candles(df)
        .line(ema, name="EMA 20", color="#f0b429", width=1)
        .volume(df)
        .add_subplot(
            Subplot(height_ratio=0.25, label="RSI(14)", y_min=0, y_max=100)
            .line(rsi, color="#58a6ff", width=1)
            .hline(70, style="dashed", color="rgba(248,81,73,0.4)")
            .hline(30, style="dashed", color="rgba(38,166,154,0.4)")
        )
    )

dash = Dashboard(title="Crypto Dashboard", cols=2, row_height=450, theme="dark")
for title, price in assets:
    dash.add(make_chart(title, price))

dash.to_html("dashboard.html")
```

---

## 8. Styles and themes

### theme

| Value | Background | Text |
|---|---|---|
| `"dark"` (default) | `#0d1117` | `#8b949e` |
| `"light"` | `#ffffff` | `#24292f` |

### candle_style

| Value | Rendering |
|---|---|
| `"classic"` (default) | Solid body, wicks |
| `"hollow"` | Transparent body on up-candles, filled body on down-candles |
| `"bars"` | OHLC bar marks (no body) |

### Line style (`style` parameter)

| Value | JS LineStyle |
|---|---|
| `"solid"` | 0 |
| `"dashed"` | 1 |
| `"dotted"` | 2 |
| `"large_dashed"` | 3 |
| `"sparse_dotted"` | 4 |

### Marker shape

`"arrowUp"` · `"arrowDown"` · `"circle"` · `"square"`

### Marker position

`"aboveBar"` · `"belowBar"` · `"inBar"`

### Y axis formats (`y_format`)

Controls the tick labels on the Y axis and the value shown in the crosshair
tooltip. Applied to all series in the pane simultaneously. Available on both
`Chart` (main pane) and `Subplot`.

| Value | Y axis display | Typical use |
|---|---|---|
| `None` (default) | Decimal number | Prices, raw indicator values |
| `"percent"` | `+3.25%` / `-1.10%` | Returns, drawdown, normalised oscillators |
| `"currency"` | `1,234.56` | P&L in dollars |
| `"bps"` | `32.0 bps` | Spreads, basis points (value × 10 000) |
| `"volume"` | `1.2M` / `850K` | Volume (lightweight-charts native) |

```python
# P&L curve with percent axis
Chart("Strategy P&L", y_format="percent")
.line(pnl_cum)

# Drawdown subplot with percent axis — full autoscale (no y_min/y_max)
Subplot(height_ratio=0.25, label="Drawdown", y_format="percent")
.area(drawdown, bottom_color="rgba(239,83,80,0.4)", line_color="#f85149")

# RSI — bounded 0–100, no special format needed
Subplot(height_ratio=0.2, label="RSI(14)", y_min=0, y_max=100)
.line(rsi, color="#58a6ff")

# Spread in basis points
Subplot(height_ratio=0.2, label="Spread", y_format="bps")
.line(spread_series, color="#c084fc")
```

### Default color palette (dark theme)

When `color=None`, colors are auto-assigned from this palette in insertion order:

```python
["#58a6ff", "#f0b429", "#a5b4fc", "#26a641", "#f85149", "#c084fc", "#fb923c", "#e879f9"]
#  blue      amber      indigo     green       red        violet     orange     fuchsia
```

---

## 9. Offline mode and packaging

### How it works

When `offline=True` (the default), the contents of
`src/lwcharts/vendor/lightweight-charts.standalone.production.js` are inlined
directly into the generated HTML as a `<script>` block. The result is a
self-contained file that requires no network access to render.

When `offline=False`, the HTML contains:
```html
<script src="https://unpkg.com/lightweight-charts@5.2.0/dist/lightweight-charts.standalone.production.js"></script>
```

### Updating the vendor JS

The vendor file is committed to the repository. To bump to a newer version of
lightweight-charts, run the update script manually:

```bash
uv run python scripts/update_vendor.py                 # updates to the default version
uv run python scripts/update_vendor.py --version 5.3.0 # specific version
```

After updating, verify that the chart and dashboard templates still work correctly.
The JS API surface may change between minor versions.

If the vendor file is missing (e.g. after a fresh `git clone` without running the
script), any import of `lwcharts` will raise a `FileNotFoundError` with instructions.
