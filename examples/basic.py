"""Bougies + EMA + volume overlay + résistance partielle + marker d'entrée."""
import pandas as pd
from lwcharts import Chart

df = pd.read_parquet("examples/data/ASSET.A.parquet")

ema_20 = df["close"].ewm(span=20).mean()
ema_50 = df["close"].ewm(span=50).mean()

resistance = pd.Series(data=45200.0, index=df.index[80:91], name="Résistance")

entries = pd.Series(False, index=df.index)
entries.iloc[40] = True
entries.iloc[120] = True

chart = (
    Chart(title="BTC/USDT — 1D", theme="dark", height=650)
    .candles(df)
    .line(ema_20, name="EMA 20", color="#f0b429", width=1)
    .line(ema_50, name="EMA 50", color="#a5b4fc", width=1, style="dashed")
    .volume(df, position="overlay")
    .line(resistance, name="Résistance", color="#f85149", style="dashed", width=2, fill_method=None)
    .hline(40000, color="rgba(38,166,154,0.4)", style="dashed", label="Support")
    .markers(entries, shape="arrowUp", position="belowBar", color="#26a641", label="E")
)

chart.serve()