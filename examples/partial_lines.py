"""
Lignes partielles et discontinues — une seule Series avec des NaN entre segments.

Démontre trois cas :
  1. Niveaux horizontaux ponctuels (une valeur par date, fill_method=None)
  2. Segments horizontaux sur une durée fixe (5 barres de trading)
  3. Ligne oblique (niveau variable sur une plage de dates)
"""
import pandas as pd
from lwcharts import Chart

df = pd.read_parquet("examples/data/ZTS.US.parquet").loc["2023-01-01":"2024-06-30"]

# ── 1. Swing highs détectés → niveaux ponctuels ──────────────────────────────
n = 15
swing_high_mask = df["high"] == df["high"].rolling(2 * n + 1, center=True).max()
swing_highs = df["high"][swing_high_mask]  # Series réduite aux ~10-15 dates

# ── 2. Chaque swing high devient un segment horizontal de 10 barres ──────────
resistance_segments = pd.Series(dtype=float, index=df.index)
for date, price in swing_highs.items():
    pos = df.index.get_loc(date)
    end_pos = min(pos + 10, len(df.index) - 1)
    end_date = df.index[end_pos]
    resistance_segments.loc[date:end_date] = price
# Les dates entre deux segments restent NaN → gap visuel automatique

# ── 3. Swing lows → segments de support ──────────────────────────────────────
swing_low_mask = df["low"] == df["low"].rolling(2 * n + 1, center=True).min()
swing_lows = df["low"][swing_low_mask]

support_segments = pd.Series(dtype=float, index=df.index)
for date, price in swing_lows.items():
    pos = df.index.get_loc(date)
    end_pos = min(pos + 10, len(df.index) - 1)
    support_segments.loc[date:df.index[end_pos]] = price

# ── 4. Ligne oblique : tendance entre deux points de swing ───────────────────
# On prend le premier et le dernier swing high pour tracer une droite de tendance
if len(swing_highs) >= 2:
    t1, p1 = swing_highs.index[0],  swing_highs.iloc[0]
    t2, p2 = swing_highs.index[-1], swing_highs.iloc[-1]
    trend_range = df.index[(df.index >= t1) & (df.index <= t2)]
    n_bars = len(trend_range)
    trend_values = pd.Series(
        [p1 + (p2 - p1) * i / (n_bars - 1) for i in range(n_bars)],
        index=trend_range,
    )
    trendline = pd.Series(dtype=float, index=df.index)
    trendline.loc[t1:t2] = trend_values
else:
    trendline = pd.Series(dtype=float, index=df.index)

# ── chart ─────────────────────────────────────────────────────────────────────
ema_20 = df["close"].ewm(span=20).mean()

chart = (
    Chart("ZTS 2023-2024 — Lignes partielles", theme="dark", height=650)
    .candles(df)
    .line(ema_20, name="EMA 20", color="#f0b429", width=1)
    # Segments de résistance (rouge, tirets) — une seule Series, NaN entre chaque
    .line(resistance_segments, name="Résistances", color="rgba(248,81,73,0.8)",
          style="dashed", width=2, fill_method=None)
    # Segments de support (vert, tirets)
    .line(support_segments, name="Supports", color="rgba(38,166,154,0.8)",
          style="dashed", width=2, fill_method=None)
    # Ligne de tendance oblique (bleu, pointillés)
    .line(trendline, name="Tendance", color="#58a6ff",
          style="dotted", width=1, fill_method=None)
    # Markers aux swing highs/lows pour repérer les points d'ancrage
    .markers(swing_high_mask, shape="arrowDown", position="aboveBar",
             color="rgba(248,81,73,0.7)", label="H")
    .markers(swing_low_mask,  shape="arrowUp",   position="belowBar",
             color="rgba(38,166,154,0.7)", label="L")
)

chart.serve()
