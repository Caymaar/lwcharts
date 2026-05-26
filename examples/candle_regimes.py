"""
Régimes de marché — couleur des bougies selon le régime EMA 20/100.

Le corps ET les mèches changent de couleur selon le régime :
  bull    → teal (peu importe le sens de la bougie)
  bear    → rouge
  neutral → couleurs up/down habituelles (NaN dans la Series)

Complété par bg_zones_from_series pour le fond de pane et un subplot RSI.
"""
import pandas as pd
from lwcharts import Chart, Subplot

df = pd.read_parquet("examples/data/ZTS.US.parquet").loc["2018-01-01":]

ema_20  = df["close"].ewm(span=20).mean()
ema_100 = df["close"].ewm(span=100).mean()

# ── régime : 3 états ──────────────────────────────────────────────────────────
regime = pd.Series("neutral", index=df.index)
regime[ema_20 > ema_100 * 1.01] = "bull"
regime[ema_20 < ema_100 * 0.99] = "bear"

palette = {
    "bull":    "rgba(38,166,154,0.08)",
    "bear":    "rgba(239,83,80,0.07)",
    "neutral": "rgba(139,148,158,0.04)",
}

# ── couleurs de bougies : override total selon le régime ──────────────────────
# NaN → la bougie garde ses couleurs up/down par défaut
candle_colors = pd.Series(index=df.index, dtype=object)
candle_colors[regime == "bull"] = "rgba(38,166,154,0.85)"
candle_colors[regime == "bear"] = "rgba(239,83,80,0.85)"

# ── indicateurs ───────────────────────────────────────────────────────────────
delta = df["close"].diff()
rsi   = 100 - 100 / (1 + delta.clip(lower=0).ewm(com=13).mean()
                           / (-delta.clip(upper=0)).ewm(com=13).mean())

chart = (
    Chart("ZTS — Couleur des bougies par régime EMA 20/100", theme="dark", height=800)
    .candles(df)
    .candle_colors(candle_colors, apply_to="both")
    .line(ema_20,  name="EMA 20",  color="#f0b429", width=1)
    .line(ema_100, name="EMA 100", color="#a5b4fc", width=2, style="dashed")
    .bg_zones_from_series(regime, palette)
    .volume(df)
    .add_subplot(
        Subplot(height_ratio=0.18, label="RSI(14)", y_min=0, y_max=100)
        .line(rsi, color="#58a6ff", width=1)
        .hline(70, color="rgba(248,81,73,0.4)", style="dashed")
        .hline(50, color="rgba(139,148,158,0.2)", style="dotted")
        .hline(30, color="rgba(38,166,154,0.4)", style="dashed")
        .bg_zones_from_series(regime, palette)
    )
)

chart.serve()
