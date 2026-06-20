"""
Markers — entrées/sorties, golden/death cross, swing highs.

Montre les trois formes d'input acceptées par .markers() :
  - pd.Series[bool] → un marker par True
  - list[dict]      → markers manuels avec forme/couleur/texte custom
  - .marker()       → un seul événement ponctuel
"""
import pandas as pd
from lwcharts import Chart, Subplot

df = pd.read_parquet("examples/data/ASSET.C.parquet").loc["2019-01-01":]

ema_20 = df["close"].ewm(span=20).mean()
ema_50 = df["close"].ewm(span=50).mean()
delta  = df["close"].diff()
rsi    = 100 - 100 / (1 + delta.clip(lower=0).ewm(com=13).mean()
                            / (-delta.clip(upper=0)).ewm(com=13).mean())

# ── signaux de croisement EMA ─────────────────────────────────────────────────
prev_20, prev_50 = ema_20.shift(1), ema_50.shift(1)
golden_cross = (ema_20 > ema_50) & (prev_20 <= prev_50)   # EMA 20 passe au-dessus
death_cross  = (ema_20 < ema_50) & (prev_20 >= prev_50)   # EMA 20 passe en-dessous

# ── swing highs (local max sur 15 jours de chaque côté) ──────────────────────
n = 15
swing_high = df["high"] == df["high"].rolling(2 * n + 1, center=True).max()
swing_low  = df["low"]  == df["low"].rolling(2 * n + 1, center=True).min()

# ── événement manuel (IPO, earnings, annonce) ─────────────────────────────────
key_events = [
    {"time": "2021-01-19", "shape": "circle",    "position": "aboveBar", "color": "#f0b429", "label": "E"},
    {"time": "2022-08-03", "shape": "circle",    "position": "aboveBar", "color": "#f0b429", "label": "E"},
    {"time": "2024-02-08", "shape": "circle",    "position": "aboveBar", "color": "#f0b429", "label": "E"},
]

chart = (
    Chart("ZTS — Markers : croisements EMA & swing highs/lows", theme="dark", height=800)
    .candles(df)
    .line(ema_20, name="EMA 20", color="#f0b429", width=1)
    .line(ema_50, name="EMA 50", color="#a5b4fc", width=1, style="dashed")
    .volume(df)
    # Golden cross : arrowUp vert sous la bougie
    .markers(golden_cross, shape="arrowUp",   position="belowBar", color="#26a641", label="G")
    # Death cross : arrowDown rouge au-dessus de la bougie
    .markers(death_cross,  shape="arrowDown", position="aboveBar", color="#f85149", label="D")
    # Swing highs : carré orange au-dessus de la bougie
    .markers(swing_high,   shape="square",    position="aboveBar", color="#f0b429", label="H")
    # Swing lows : carré bleu sous la bougie
    .markers(swing_low,    shape="square",    position="belowBar", color="#58a6ff", label="L")
    # Earnings (liste de dicts)
    .markers(key_events)
    .add_subplot(
        Subplot(height_ratio=0.18, label="RSI(14)", y_min=0, y_max=100)
        .line(rsi, color="#58a6ff", width=1)
        .hline(70, color="rgba(248,81,73,0.4)", style="dashed")
        .hline(30, color="rgba(38,166,154,0.4)", style="dashed")
    )
)

chart.serve()
