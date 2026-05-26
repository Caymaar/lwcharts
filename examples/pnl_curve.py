"""
Courbe de P&L — stratégie momentum sur ZTS.US.

Stratégie : long quand close > EMA 20, flat sinon (signal J-1).
  - Pane principal  : equity curve (area) + buy & hold en comparaison
  - Subplot 1       : drawdown (area, y_format="percent")
  - Subplot 2       : returns journaliers stratégie vs buy & hold (histogrammes)

Illustre :
  - Chart sans bougies (séries pures)
  - bg_zones_from_mask sur le pane principal
  - y_format="percent" sur les subplots
  - Deux histogrammes superposés dans le même pane
"""
import pandas as pd
from lwcharts import Chart, Subplot

df = pd.read_parquet("examples/data/ZTS.US.parquet")

ema_20 = df["close"].ewm(span=20).mean()

# ── stratégie momentum ────────────────────────────────────────────────────────
daily_ret  = df["close"].pct_change()
in_pos     = (df["close"] > ema_20).shift(1).fillna(False)
strat_ret  = (daily_ret * in_pos).fillna(0)
bh_ret     = daily_ret.fillna(0)

# Courbes cumulées (base 100)
strat_equity = (1 + strat_ret).cumprod() * 100
bh_equity    = (1 + bh_ret).cumprod() * 100

# Drawdown stratégie
dd = ((strat_equity / strat_equity.cummax()) - 1).rename("Drawdown")

# Returns en % pour les histogrammes
strat_ret_pct = strat_ret * 100
bh_ret_pct    = bh_ret    * 100

# ── annotations ───────────────────────────────────────────────────────────────
# Pire drawdown
worst_dd_date = dd.idxmin()
worst_dd_val  = dd.min()

# Pic d'equity
peak_date = strat_equity.idxmax()

chart = (
    Chart("ZTS — Momentum EMA 20 : equity curve", theme="dark", height=750, y_format="percent")
    # Equity stratégie (area bleue)
    .area(
        strat_equity,
        name="Stratégie",
        top_color="rgba(88,166,255,0.18)",
        bottom_color="rgba(88,166,255,0.0)",
        line_color="#58a6ff",
    )
    # Buy & hold en comparaison (ligne pointillée)
    .line(bh_equity, name="Buy & Hold", color="#8b949e", width=1, style="dashed")
    .hline(100, color="rgba(139,148,158,0.3)", style="solid")
    # Fond vert quand la stratégie est en gain, rouge sinon
    .bg_zones_from_mask(
        strat_equity > 100,
        color_true="rgba(38,166,154,0.05)",
        color_false="rgba(239,83,80,0.05)",
    )
    # Marker au pic de l'equity
    .marker(peak_date, shape="circle", position="aboveBar", color="#f0b429", label="P")
    .add_subplot(
        Subplot(height_ratio=0.22, label="Drawdown", y_format="percent")
        .area(
            dd,
            top_color="rgba(239,83,80,0.0)",
            bottom_color="rgba(239,83,80,0.45)",
            line_color="#f85149",
        )
        .hline(0, color="rgba(139,148,158,0.3)", style="solid")
        # Marker au pire drawdown
    )
    .add_subplot(
        Subplot(height_ratio=0.20, label="Returns journaliers (%)", y_format="percent")
        .histogram(strat_ret_pct, name="Stratégie", color_up="#26a641", color_down="#f85149")
        .histogram(bh_ret_pct,    name="Buy & Hold", color="rgba(139,148,158,0.35)")
        .hline(0, color="rgba(139,148,158,0.3)", style="solid")
    )
)

# Marker au pire drawdown (ajout sur le subplot drawdown pas possible en v1,
# on place un marker sur le pane principal à la même date pour signaler le creux)
chart.marker(worst_dd_date, shape="arrowDown", position="aboveBar",
             color="#f85149", label="DD")

chart.serve()
