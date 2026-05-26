"""RSI + MACD + Stochastique empilés."""
import pandas as pd
from lwcharts import Chart, Subplot

df = pd.read_parquet("examples/data/ZQK.US.parquet")  # --- REPLACE WITH SYNTHETIC DATA ---

# RSI
delta = df["close"].diff()
gain = delta.clip(lower=0).ewm(com=13).mean()
loss = (-delta.clip(upper=0)).ewm(com=13).mean()
rsi = 100 - 100 / (1 + gain / loss)

# MACD
ema_fast = df["close"].ewm(span=12).mean()
ema_slow = df["close"].ewm(span=26).mean()
macd_line = ema_fast - ema_slow
signal = macd_line.ewm(span=9).mean()
macd_hist = macd_line - signal

# Stochastique
low_14 = df["low"].rolling(14).min()
high_14 = df["high"].rolling(14).max()
stoch_k = 100 * (df["close"] - low_14) / (high_14 - low_14)
stoch_d = stoch_k.rolling(3).mean()

chart = (
    Chart("BTC/USDT — Analyse technique", theme="dark", height=700)
    .candles(df)
    .line(df["close"].ewm(span=20).mean(), name="EMA 20", color="#f0b429")
    .volume(df)
    .add_subplot(
        Subplot(height_ratio=0.18, label="RSI(14)", y_min=0, y_max=100)
        .line(rsi, color="#58a6ff")
        .hline(70, color="rgba(248,81,73,0.4)", style="dashed")
        .hline(30, color="rgba(38,166,154,0.4)", style="dashed")
    )
    .add_subplot(
        Subplot(height_ratio=0.20, label="MACD(12,26,9)")
        .histogram(macd_hist, color_up="#26a641", color_down="#f85149")
        .line(macd_line, name="MACD", color="#58a6ff")
        .line(signal, name="Signal", color="#f0b429", style="dashed")
        .hline(0, color="rgba(139,148,158,0.3)")
    )
    .add_subplot(
        Subplot(height_ratio=0.15, label="Stoch(14,3)", y_min=0, y_max=100, y_format="percent")
        .line(stoch_k, name="%K", color="#a5b4fc")
        .line(stoch_d, name="%D", color="#f0b429", style="dashed")
        .hline(80, style="dashed")
        .hline(20, style="dashed")
    )
)

chart.serve(port=1338)
