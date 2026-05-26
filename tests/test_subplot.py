import pandas as pd
import pytest
from lwcharts import Chart, Subplot
from lwcharts.renderer import _build_config


def _make_series(n: int = 10, start: float = 50.0) -> pd.Series:
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    return pd.Series([start + i for i in range(n)], index=idx)


def _make_df(n: int = 10) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = [100.0 + i for i in range(n)]
    return pd.DataFrame(
        {"open": close, "high": [c + 1 for c in close],
         "low": [c - 1 for c in close], "close": close,
         "volume": [1_000_000.0] * n},
        index=idx,
    )


def test_subplot_line_returns_self():
    sp = Subplot()
    result = sp.line(_make_series())
    assert result is sp


def test_subplot_hline_returns_self():
    sp = Subplot()
    result = sp.hline(70.0)
    assert result is sp


def test_subplot_histogram_color_up_down():
    s = pd.Series([-1.0, 0.0, 1.0], index=pd.date_range("2024-01-01", periods=3, freq="B"))
    sp = Subplot()
    sp.histogram(s, color_up="#green", color_down="#red")
    data = sp._series[0].data
    assert data[2]["color"] == "#green"
    assert data[0]["color"] == "#red"
    assert data[1]["color"] == "rgba(139,148,158,0.5)"


def test_subplot_auto_color_assigned():
    sp = Subplot()
    sp.line(_make_series())
    sp.line(_make_series())
    colors = [s.color for s in sp._series]
    assert colors[0] != colors[1]


def test_chart_add_subplot_inherits_candle_index():
    df = _make_df()
    s = _make_series()
    chart = Chart("Test").candles(df)
    sp = Subplot().line(s)
    chart.add_subplot(sp)
    assert sp._candle_index is not None


def test_subplot_before_candles_no_candle_index():
    sp = Subplot().line(_make_series())
    assert sp._candle_index is None


def test_build_config_subpanes():
    df = _make_df()
    s = _make_series()
    chart = (
        Chart("Test", height=700)
        .candles(df)
        .add_subplot(
            Subplot(height_ratio=0.2, label="RSI", y_min=0, y_max=100)
            .line(s, color="#58a6ff")
            .hline(70.0, style="dashed")
        )
    )
    config = _build_config(chart)
    assert len(config["subPanes"]) == 1
    sp_cfg = config["subPanes"][0]
    assert sp_cfg["label"] == "RSI"
    assert sp_cfg["yMin"] == 0
    assert sp_cfg["yMax"] == 100
    assert len(sp_cfg["series"]) == 1
    assert len(sp_cfg["hlines"]) == 1


def test_subplot_area():
    sp = Subplot()
    sp.area(_make_series(), top_color="rgba(0,0,0,0.2)", line_color="#fff")
    assert sp._series[0].to_dict()["type"] == "area"


def test_subplot_baseline():
    sp = Subplot()
    sp.baseline(_make_series(), base=0.0)
    assert sp._series[0].to_dict()["type"] == "baseline"
