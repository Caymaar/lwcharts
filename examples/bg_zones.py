"""Zones de fond colorées — bg_zone, bg_zones, bg_zones_from_series, bg_zones_from_mask."""
import numpy as np
import pandas as pd
from lwcharts import Chart, Subplot

df = pd.read_parquet("examples/data/ASSET.A.parquet")  # --- REPLACE WITH SYNTHETIC DATA ---

# ── indicateurs ──────────────────────────────────────────────────────────────
ema_20 = df["close"].ewm(span=20).mean()
ema_50 = df["close"].ewm(span=50).mean()

delta = df["close"].diff()
gain = delta.clip(lower=0).ewm(com=13).mean()
loss = (-delta.clip(upper=0)).ewm(com=13).mean()
rsi = 100 - 100 / (1 + gain / loss)

# ── régime de marché (3 états) ────────────────────────────────────────────────
# Simple heuristique : EMA20 vs EMA50
regime = pd.Series(index=df.index, dtype=object)
regime[ema_20 > ema_50 * 1.005] = "bull"
regime[ema_20 < ema_50 * 0.995] = "bear"
regime[regime.isna()] = "neutral"

palette = {
    "bull":    "rgba(38,166,154,0.10)",   # vert translucide
    "bear":    "rgba(239,83,80,0.08)",    # rouge translucide
    "neutral": "rgba(240,180,41,0.06)",   # ambre translucide
}

# ── masque booléen : periodes de forte volatilité ─────────────────────────────
vol_mask = df["close"].pct_change().rolling(10).std() > 0.018

chart = (
    Chart("BTC — Background Zones", theme="dark", height=750)
    .candles(df)
    .line(ema_20, name="EMA 20", color="#f0b429", width=1)
    .line(ema_50, name="EMA 50", color="#a5b4fc", width=1, style="dashed")
    .volume(df, position="pane")
    # Zones régime sur le pane principal (depuis Series catégorielle)
    .bg_zones_from_series(regime, palette)
    .add_subplot(
        Subplot(height_ratio=0.20, label="RSI(14)", y_min=0, y_max=100)
        .line(rsi, color="#58a6ff")
        .hline(70, color="rgba(248,81,73,0.4)", style="dashed")
        .hline(30, color="rgba(38,166,154,0.4)", style="dashed")
        # Zones de forte volatilité sur le subplot RSI (masque booléen)
        .bg_zones_from_mask(
            vol_mask,
            color_true="rgba(240,180,41,0.15)",
        )
    )
)

chart.serve(port=1338)
