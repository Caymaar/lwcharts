"""
Spread entre deux actifs — ZTS.US vs ZS.US (2018-2026).

Pane principal : les deux closes normalisés à 100 (performance relative).
  - Fond coloré selon quel actif surperforme
Subplot 1 : spread (ZTS_norm - ZS_norm) en baseline autour de 0.
  - Zone verte quand ZTS surperforme, rouge sinon
Subplot 2 : corrélation glissante 60 jours entre les deux séries.

Illustre :
  - Chart sans bougies (séries de closes uniquement)
  - bg_zones_from_mask sur le pane principal
  - baseline avec fill coloré au-dessus/en-dessous de zéro
  - y_format="percent" sur le subplot corrélation
"""
import pandas as pd
from lwcharts import Chart, Subplot

zts = pd.read_parquet("examples/data/ZTS.US.parquet")
zs  = pd.read_parquet("examples/data/ZS.US.parquet")

# Intersection des dates de trading (les deux actifs ont le même calendrier ici)
common = zts.index.intersection(zs.index)
zts_c = zts.loc[common, "close"]
zs_c  = zs.loc[common, "close"]

# Normalisation à 100 à la première date commune
zts_norm = zts_c / zts_c.iloc[0] * 100
zs_norm  = zs_c  / zs_c.iloc[0]  * 100

# Spread (différence de performance cumulée)
spread = (zts_norm - zs_norm).rename("ZTS − ZS")

# Corrélation glissante 60 jours sur les returns
zts_ret = zts_c.pct_change()
zs_ret  = zs_c.pct_change()
rolling_corr = zts_ret.rolling(60).corr(zs_ret).rename("Corr 60j")

# ZTS outperforms quand son index normalisé est supérieur
zts_outperforms = zts_norm > zs_norm

chart = (
    Chart("ZTS vs ZS — Performance relative (base 100)", theme="dark", height=750)
    # Pane principal : closes normalisés (pas de bougies)
    .line(zts_norm, name="ZTS.US", color="#58a6ff", width=2)
    .line(zs_norm,  name="ZS.US",  color="#f0b429", width=2)
    .hline(100, color="rgba(139,148,158,0.3)", style="solid")
    # Fond coloré selon le leader
    .bg_zones_from_mask(
        zts_outperforms,
        color_true="rgba(88,166,255,0.06)",    # ZTS devant → bleu
        color_false="rgba(240,180,41,0.06)",   # ZS devant → ambre
    )
    .add_subplot(
        Subplot(height_ratio=0.25, label="Spread ZTS − ZS (pts base 100)")
        .baseline(spread, base=0.0, name="Spread")
        .hline(0, color="rgba(139,148,158,0.3)", style="solid")
    )
    .add_subplot(
        Subplot(height_ratio=0.18, label="Corrélation glissante 60j", y_min=-1, y_max=1)
        .line(rolling_corr, color="#c084fc", width=1)
        .hline( 0.8, color="rgba(38,166,154,0.4)",  style="dashed", label="+0.8")
        .hline( 0.0, color="rgba(139,148,158,0.3)", style="solid")
        .hline(-0.5, color="rgba(248,81,73,0.4)",   style="dashed", label="-0.5")
    )
)

chart.serve()
