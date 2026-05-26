"""Multi-timeframe : bougies daily + bougies weekly dans un subplot dédié."""
import pandas as pd
from lwcharts import Chart, Subplot

df_daily = pd.read_parquet("examples/data/ZQK.US.parquet")  # --- REPLACE WITH SYNTHETIC DATA ---

# Resample en weekly (chaque lundi)
df_weekly = df_daily.resample("W-MON").agg(
    {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
).dropna()

# Indicateurs daily
ema_20d = df_daily["close"].ewm(span=20).mean()

delta = df_daily["close"].diff()
gain = delta.clip(lower=0).ewm(com=13).mean()
loss = (-delta.clip(upper=0)).ewm(com=13).mean()
rsi = 100 - 100 / (1 + gain / loss)

# Régime weekly (EMA 5 vs EMA 13 sur weekly)
ema5w = df_weekly["close"].ewm(span=5).mean()
ema13w = df_weekly["close"].ewm(span=13).mean()
regime_w = pd.Series("neutral", index=df_weekly.index)
regime_w[ema5w > ema13w] = "bull"
regime_w[ema5w < ema13w] = "bear"

# Répercution du régime weekly sur l'index daily via ffill
regime_daily = regime_w.reindex(df_daily.index, method="ffill").fillna("neutral")

palette = {
    "bull":    "rgba(38,166,154,0.09)",
    "bear":    "rgba(239,83,80,0.07)",
    "neutral": "rgba(139,148,158,0.04)",
}

chart = (
    Chart("Daily + Weekly — Multi-Timeframe", theme="dark", height=850)
    .candles(df_daily)
    .line(ema_20d, name="EMA 20D", color="#f0b429", width=1)
    .volume(df_daily, position="overlay")
    # Fond coloré selon le régime weekly sur le chart daily
    .bg_zones_from_series(regime_daily, palette)
    # Subplot avec les bougies weekly
    .add_subplot(
        Subplot(height_ratio=0.30, label="Weekly")
        .candles(df_weekly, style="hollow", up_color="#26a641", down_color="#f85149")
        .line(ema5w,  name="EMA 5W",  color="#f0b429", width=1)
        .line(ema13w, name="EMA 13W", color="#a5b4fc", width=1, style="dashed")
        # Même fond régime sur le subplot weekly
        .bg_zones_from_series(regime_w, palette)
    )
    .add_subplot(
        Subplot(height_ratio=0.15, label="RSI(14)", y_min=0, y_max=100)
        .line(rsi, color="#58a6ff")
        .hline(70, color="#bcf000", style="dashed")
        .hline(30, color="#05ec61", style="dashed")
    )
)

chart.serve(port=1338)
