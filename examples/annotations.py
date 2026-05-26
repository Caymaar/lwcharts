"""Markers, candle_colors (zones de danger, régime de marché)."""
import pandas as pd
from lwcharts import Chart

df = pd.read_parquet("data/ZQK.US.parquet")

danger_mask = df["close"].pct_change().rolling(5).std() > 0.015

candle_colors = pd.Series(index=df.index, dtype=object)
candle_colors[danger_mask] = "rgba(255,140,0,0.7)"

chart = (
    Chart("BTC — Annotations", theme="dark", height=600)
    .candles(df)
    .candle_colors(candle_colors)
    .markers(
        [
            {"time": str(df.index[60].date()), "shape": "circle", "position": "aboveBar", "color": "#f0b429", "label": "P"},
            {"time": str(df.index[150].date()), "shape": "arrowDown", "position": "aboveBar", "color": "#f85149", "label": "X"},
            {"time": str(df.index[200].date()), "shape": "arrowUp", "position": "belowBar", "color": "#26a641", "label": "E"},
        ]
    )
    .hline(50000, label="Résistance", color="rgba(240,180,41,0.5)")
    .hline(38000, label="Support", color="rgba(38,166,154,0.4)", style="dashed")
)

chart.serve()
