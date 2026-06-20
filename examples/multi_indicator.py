"""
Analyse technique complète — ASSET.C avec stacking de subplots.

Démontre la densité d'informations possible dans un seul Chart :
  - Bougies creux (hollow candles) + EMA 20/50/200
  - Volume en overlay (fond de pane)
  - Fond coloré selon le régime EMA 50/200
  - RSI avec zones de survente/surachat
  - MACD histogramme + signal line
  - Bollinger %B (oscillateur 0–1)
  - ATR normalisé en % du close
"""
import pandas as pd
from lwcharts import Chart, Subplot

df = pd.read_parquet("examples/data/ASSET.C.parquet").loc["2019-01-01":]

# ── indicateurs ───────────────────────────────────────────────────────────────
ema_20  = df["close"].ewm(span=20).mean()
ema_50  = df["close"].ewm(span=50).mean()
ema_200 = df["close"].ewm(span=200).mean()

# RSI(14)
delta   = df["close"].diff()
rsi     = 100 - 100 / (1 + delta.clip(lower=0).ewm(com=13).mean()
                              / (-delta.clip(upper=0)).ewm(com=13).mean())

# MACD(12,26,9)
macd_line  = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()
signal     = macd_line.ewm(span=9).mean()
macd_hist  = macd_line - signal

# Bollinger Bands %B
bb_mid = df["close"].rolling(20).mean()
bb_std = df["close"].rolling(20).std()
bb_up  = bb_mid + 2 * bb_std
bb_low = bb_mid - 2 * bb_std
bb_pct_b = (df["close"] - bb_low) / (bb_up - bb_low)

# ATR(14) normalisé en % du close
tr = pd.concat([
    df["high"] - df["low"],
    (df["high"] - df["close"].shift(1)).abs(),
    (df["low"]  - df["close"].shift(1)).abs(),
], axis=1).max(axis=1)
atr_pct = (tr.ewm(span=14).mean() / df["close"] * 100).rename("ATR%")

# ── régime pour le fond ───────────────────────────────────────────────────────
regime = pd.Series("neutral", index=df.index)
regime[ema_50 > ema_200 * 1.005] = "bull"
regime[ema_50 < ema_200 * 0.995] = "bear"
palette = {
    "bull":    "rgba(38,166,154,0.06)",
    "bear":    "rgba(239,83,80,0.05)",
    "neutral": "rgba(139,148,158,0.03)",
}

chart = (
    Chart("ASSET.C — Analyse technique complète (2019+)", theme="dark",
          height=1100, candle_style="hollow")
    .candles(df)
    .line(ema_20,  name="EMA 20",  color="#f0b429", width=1)
    .line(ema_50,  name="EMA 50",  color="#a5b4fc", width=1, style="dashed")
    .line(ema_200, name="EMA 200", color="#fb923c", width=2, style="dashed")
    .volume(df, position="overlay")
    .bg_zones_from_series(regime, palette)
    .add_subplot(
        Subplot(height_ratio=0.14, label="RSI(14)", y_min=0, y_max=100)
        .line(rsi, color="#58a6ff", width=1)
        .hline(70, color="rgba(248,81,73,0.4)",   style="dashed")
        .hline(50, color="rgba(139,148,158,0.2)", style="dotted")
        .hline(30, color="rgba(38,166,154,0.4)",  style="dashed")
        .bg_zones_from_series(regime, palette)
    )
    .add_subplot(
        Subplot(height_ratio=0.16, label="MACD(12,26,9)")
        .histogram(macd_hist, color_up="#26a641", color_down="#f85149")
        .line(macd_line, name="MACD",   color="#58a6ff", width=1)
        .line(signal,    name="Signal", color="#f0b429", width=1, style="dashed")
        .hline(0, color="rgba(139,148,158,0.3)", style="solid")
    )
    .add_subplot(
        Subplot(height_ratio=0.12, label="Bollinger %B", y_min=0, y_max=1)
        .line(bb_pct_b, color="#c084fc", width=1)
        .hline(1.0, color="rgba(248,81,73,0.4)",   style="dashed", label="BB haut")
        .hline(0.5, color="rgba(139,148,158,0.25)", style="dotted")
        .hline(0.0, color="rgba(38,166,154,0.4)",  style="dashed", label="BB bas")
    )
    .add_subplot(
        Subplot(height_ratio=0.10, label="ATR(%)", y_format="percent")
        .area(
            atr_pct,
            top_color="rgba(251,146,60,0.25)",
            bottom_color="rgba(251,146,60,0.0)",
            line_color="#fb923c",
        )
    )
)

chart.serve()
