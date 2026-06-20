"""
Points pivots & niveaux clés.

Deux approches complémentaires :
  1. Pivots classiques hebdomadaires (P, R1, R2, S1, S2) tracés comme des
     lignes partielles (fill_method=None) — ne s'affichent que pour la semaine
     à laquelle elles appartiennent.
  2. Swing highs/lows (extrema locaux) détectés sur 10 jours de chaque côté,
     affichés comme markers avec le niveau de prix en label.
"""
import pandas as pd
from lwcharts import Chart, Subplot

df = pd.read_parquet("examples/data/ASSET.C.parquet").loc["2022-01-01":]

# ── pivots hebdomadaires ──────────────────────────────────────────────────────
weekly = df.resample("W-FRI").agg({"high": "max", "low": "min", "close": "last"})

# Calcul des niveaux pivot sur la semaine précédente
weekly["P"]  = (weekly["high"].shift(1) + weekly["low"].shift(1) + weekly["close"].shift(1)) / 3
weekly["R1"] = 2 * weekly["P"] - weekly["low"].shift(1)
weekly["R2"] = weekly["P"] + (weekly["high"].shift(1) - weekly["low"].shift(1))
weekly["S1"] = 2 * weekly["P"] - weekly["high"].shift(1)
weekly["S2"] = weekly["P"] - (weekly["high"].shift(1) - weekly["low"].shift(1))
weekly = weekly.dropna()

# Répercussion sur l'index daily via ffill — chaque lundi reprend les pivots du vendredi
def weekly_to_daily(series: pd.Series) -> pd.Series:
    return series.reindex(df.index, method="ffill")

p_daily  = weekly_to_daily(weekly["P"])
r1_daily = weekly_to_daily(weekly["R1"])
r2_daily = weekly_to_daily(weekly["R2"])
s1_daily = weekly_to_daily(weekly["S1"])
s2_daily = weekly_to_daily(weekly["S2"])

# ── swing highs/lows (extrema locaux) ────────────────────────────────────────
n = 10
swing_high_mask = (df["high"] == df["high"].rolling(2 * n + 1, center=True).max()) & df["high"].notna()
swing_low_mask  = (df["low"]  == df["low"].rolling(2 * n + 1, center=True).min())  & df["low"].notna()

# Derniers niveaux swing comme hlines permanentes (support/résistance clés)
last_highs = df["high"][swing_high_mask].tail(2)
last_lows  = df["low"][swing_low_mask].tail(2)

# ── indicateurs ───────────────────────────────────────────────────────────────
ema_20 = df["close"].ewm(span=20).mean()
delta  = df["close"].diff()
rsi    = 100 - 100 / (1 + delta.clip(lower=0).ewm(com=13).mean()
                            / (-delta.clip(upper=0)).ewm(com=13).mean())

chart = (
    Chart("ZTS — Pivots hebdomadaires & swing highs/lows", theme="dark", height=850)
    .candles(df)
    .line(ema_20, name="EMA 20", color="#f0b429", width=1)
    # Niveaux pivot hebdomadaires (fill_method="ffill" = step function semaine par semaine)
    .line(p_daily,  name="Pivot P",  color="rgba(139,148,158,0.7)", width=1, style="dashed",      fill_method="ffill")
    .line(r1_daily, name="R1",       color="rgba(248,81,73,0.55)",  width=1, style="dotted",       fill_method="ffill")
    .line(r2_daily, name="R2",       color="rgba(248,81,73,0.35)",  width=1, style="sparse_dotted",fill_method="ffill")
    .line(s1_daily, name="S1",       color="rgba(38,166,154,0.55)", width=1, style="dotted",       fill_method="ffill")
    .line(s2_daily, name="S2",       color="rgba(38,166,154,0.35)", width=1, style="sparse_dotted",fill_method="ffill")
    # Swing highs/lows comme markers
    .markers(swing_high_mask, shape="arrowDown", position="aboveBar", color="rgba(248,81,73,0.8)",  label="H")
    .markers(swing_low_mask,  shape="arrowUp",   position="belowBar", color="rgba(38,166,154,0.8)", label="L")
    # Derniers niveaux swing comme lignes de support/résistance permanentes
)

for level in last_highs:
    chart.hline(level, color="rgba(248,81,73,0.35)", style="dashed", label=f"R {level:.1f}")
for level in last_lows:
    chart.hline(level, color="rgba(38,166,154,0.35)", style="dashed", label=f"S {level:.1f}")

chart = (
    chart
    .volume(df)
    .add_subplot(
        Subplot(height_ratio=0.18, label="RSI(14)", y_min=0, y_max=100)
        .line(rsi, color="#58a6ff", width=1)
        .hline(70, color="rgba(248,81,73,0.4)", style="dashed")
        .hline(30, color="rgba(38,166,154,0.4)", style="dashed")
    )
)

chart.serve()
