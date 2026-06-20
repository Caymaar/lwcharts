"""
Close seul — séries de prix sans bougies.

Quatre variantes sur le même jeu de données ASSET.C :
  1. close_chart    : close brut en area, EMA overlay, hline au niveau IPO
  2. returns_chart  : returns cumulés (baseline autour de 0%)
  3. zscore_chart   : z-score glissant du close (oscillateur standalone)
  4. multi_chart    : ZTS + ZS normalisés à 100 sur le même pane, sans bougies

Le script sert le dernier (multi_chart). Changer la dernière ligne pour
afficher les autres.
"""
import pandas as pd
from lwcharts import Chart, Subplot

zts = pd.read_parquet("examples/data/ASSET.C.parquet")
zs  = pd.read_parquet("examples/data/ASSET.B.parquet")

# ── 1. Close brut avec EMA et niveau de référence ────────────────────────────
ema_50   = zts["close"].ewm(span=50).mean()
ema_200  = zts["close"].ewm(span=200).mean()
ipo_price = zts["close"].iloc[0]

close_chart = (
    Chart("ASSET.C — Close seul", theme="dark", height=500)
    .area(
        zts["close"],
        name="Close",
        top_color="rgba(88,166,255,0.15)",
        bottom_color="rgba(88,166,255,0.0)",
        line_color="#58a6ff",
    )
    .line(ema_50,  name="EMA 50",  color="#f0b429", width=1)
    .line(ema_200, name="EMA 200", color="#a5b4fc", width=1, style="dashed")
    .hline(ipo_price, color="rgba(139,148,158,0.4)", style="dashed",
           label=f"IPO ref {ipo_price:.1f}")
)

# ── 2. Returns cumulés en baseline ───────────────────────────────────────────
cum_returns = ((1 + zts["close"].pct_change().fillna(0)).cumprod() - 1) * 100

returns_chart = (
    Chart("ASSET.C — Returns cumulés (%)", theme="dark", height=450, y_format="percent")
    .baseline(cum_returns, base=0.0, name="Returns cumulés")
    .hline(0, color="rgba(139,148,158,0.3)", style="solid")
)

# ── 3. Z-score glissant du close ─────────────────────────────────────────────
window = 252   # 1 an de trading
zscore = (
    (zts["close"] - zts["close"].rolling(window).mean())
    / zts["close"].rolling(window).std()
).rename("Z-score 252j")

zscore_chart = (
    Chart("ASSET.C — Z-score du close (fenêtre 252j)", theme="dark", height=450)
    .line(zscore, color="#c084fc", width=1)
    .hline( 2, color="rgba(248,81,73,0.5)",   style="dashed", label="+2σ")
    .hline( 1, color="rgba(248,81,73,0.25)",  style="dotted", label="+1σ")
    .hline( 0, color="rgba(139,148,158,0.3)", style="solid")
    .hline(-1, color="rgba(38,166,154,0.25)", style="dotted", label="-1σ")
    .hline(-2, color="rgba(38,166,154,0.5)",  style="dashed", label="-2σ")
    .bg_zones_from_mask(
        zscore > 0,
        color_true="rgba(88,166,255,0.04)",
        color_false="rgba(239,83,80,0.04)",
    )
)

# ── 4. Comparaison multi-actifs normalisés à 100 ─────────────────────────────
common = zts.index.intersection(zs.index)
zts_n = zts.loc[common, "close"] / zts.loc[common, "close"].iloc[0] * 100
zs_n  = zs.loc[common,  "close"] / zs.loc[common,  "close"].iloc[0] * 100

# Volatilité glissante 21j (en %)
zts_vol = zts.loc[common, "close"].pct_change().rolling(21).std() * 100
zs_vol  = zs.loc[common,  "close"].pct_change().rolling(21).std() * 100

multi_chart = (
    Chart("ZTS vs ZS — Closes normalisés (base 100)", theme="dark", height=650)
    .line(zts_n, name="ASSET.C", color="#58a6ff", width=2)
    .line(zs_n,  name="ASSET.B",  color="#f0b429", width=2)
    .hline(100, color="rgba(139,148,158,0.3)", style="solid")
    .bg_zones_from_mask(
        zts_n > zs_n,
        color_true="rgba(88,166,255,0.05)",
        color_false="rgba(240,180,41,0.05)",
    )
    .add_subplot(
        Subplot(height_ratio=0.25, label="Volatilité 21j (%)", y_format="percent")
        .line(zts_vol, name="ZTS vol", color="#58a6ff", width=1)
        .line(zs_vol,  name="ZS vol",  color="#f0b429", width=1, style="dashed")
    )
)

# Changer ici pour visualiser les autres charts :
# close_chart.serve() / returns_chart.serve() / zscore_chart.serve()
multi_chart.serve()
