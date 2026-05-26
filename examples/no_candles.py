"""Charts sans bougies — séries standalone : P&L, equity curve, drawdown, baseline."""
import numpy as np
import pandas as pd
from lwcharts import Chart, Subplot

rng = np.random.default_rng(0)
n = 500
idx = pd.date_range("2022-01-01", periods=n, freq="B")

# ── données synthétiques ──────────────────────────────────────────────────────
returns_strat = rng.normal(0.0005, 0.012, n)
returns_bench = rng.normal(0.0003, 0.009, n)

pnl_cum   = pd.Series((1 + returns_strat).cumprod() - 1, index=idx, name="P&L cumulé")
bench_cum = pd.Series((1 + returns_bench).cumprod() - 1, index=idx, name="Benchmark")
equity    = pd.Series((1 + returns_strat).cumprod() * 100_000, index=idx, name="Equity")
drawdown  = (equity / equity.cummax() - 1).rename("Drawdown")
excess    = (pnl_cum - bench_cum).rename("Excess Return")


# ── 1. Close seul ─────────────────────────────────────────────────────────────
close_chart = (
    Chart("Close seul — aucune bougie", theme="dark", height=350)
    .line(equity, name="Equity", color="#58a6ff", width=2)
    .hline(100_000, color="rgba(139,148,158,0.4)", style="solid")
)


# ── 2. P&L cumulé avec bg_zones_from_mask ────────────────────────────────────
pnl_chart = (
    Chart("Stratégie momentum — P&L cumulé", theme="dark", height=400)
    .line(pnl_cum, name="P&L cumulé", color="#58a6ff", width=2)
    .hline(0, color="rgba(139,148,158,0.4)", style="solid")
    .bg_zones_from_mask(
        pnl_cum > 0,
        color_true="rgba(38,166,154,0.06)",
        color_false="rgba(239,83,80,0.06)",
    )
)


# ── 3. P&L vs Benchmark ──────────────────────────────────────────────────────
vs_bench_chart = (
    Chart("P&L vs Benchmark", theme="dark", height=400)
    .line(pnl_cum,   name="Stratégie",  color="#58a6ff", width=2)
    .line(bench_cum, name="Benchmark",  color="#8b949e", width=1, style="dashed")
    .hline(0, color="rgba(139,148,158,0.3)", style="solid")
)


# ── 4. Baseline — Excess Return autour de zéro ───────────────────────────────
baseline_chart = (
    Chart("Excess Return vs Benchmark", theme="dark", height=400)
    .baseline(excess, base=0.0, name="Excess Return")
)


# ── 5. Equity curve + drawdown en subplot ────────────────────────────────────
equity_chart = (
    Chart("Equity Curve + Drawdown", theme="dark", height=600)
    .line(equity, name="Equity", color="#58a6ff", width=2)
    .add_subplot(
        Subplot(height_ratio=0.3, label="Drawdown", y_format="percent")
        .area(
            drawdown,
            top_color="rgba(239,83,80,0.0)",
            bottom_color="rgba(239,83,80,0.4)",
            line_color="#f85149",
        )
    )
)


# ── serve le dernier (le plus complet) ───────────────────────────────────────
# Pour voir les autres, remplacer equity_chart par le chart voulu.
equity_chart.serve(port=1338)
