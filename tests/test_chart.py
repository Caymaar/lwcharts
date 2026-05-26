import pandas as pd
import pytest
from lwcharts import Chart
from lwcharts.renderer import _build_config


def _make_df(n: int = 10) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = [100.0 + i for i in range(n)]
    return pd.DataFrame(
        {"open": close, "high": [c + 1 for c in close],
         "low": [c - 1 for c in close], "close": close,
         "volume": [1_000_000.0] * n},
        index=idx,
    )


def test_chart_candles_auto_detect():
    df = _make_df()
    chart = Chart("Test").candles(df)
    assert chart._candle_def is not None
    assert len(chart._candle_def.data) == 10


def test_chart_candles_explicit_cols():
    df = _make_df().rename(columns={"open": "o2", "high": "h2", "low": "l2", "close": "c2"})
    chart = Chart("Test").candles(df, open="o2", high="h2", low="l2", close="c2")
    assert len(chart._candle_def.data) == 10


def test_chart_line_returns_self():
    df = _make_df()
    chart = Chart("Test").candles(df)
    result = chart.line(df["close"], name="Close")
    assert result is chart


def test_chart_chaining():
    df = _make_df()
    chart = (
        Chart("Test")
        .candles(df)
        .line(df["close"], name="Close", color="#fff")
        .hline(100.0, label="Level")
    )
    assert len(chart._overlays) == 1
    assert len(chart._hlines) == 1


def test_build_config_structure():
    df = _make_df()
    chart = Chart("Test", height=700).candles(df)
    config = _build_config(chart)
    assert config["title"] == "Test"
    assert config["totalHeight"] == 700
    assert "mainPane" in config
    assert "subPanes" in config
    assert len(config["mainPane"]["candles"]) == 10


def test_build_config_main_pane_height_floor():
    df = _make_df()
    from lwcharts import Subplot
    chart = (
        Chart("Test", height=700)
        .candles(df)
        .add_subplot(Subplot(height_ratio=0.4))
        .add_subplot(Subplot(height_ratio=0.4))
    )
    config = _build_config(chart)
    # sub_ratio_sum = 0.8, main_ratio = max(0.2, 0.35) = 0.35
    assert config["mainPaneHeight"] == int(700 * 0.35)


def test_chart_markers_bool_series():
    df = _make_df()
    entries = pd.Series(False, index=df.index)
    entries.iloc[2] = True
    entries.iloc[5] = True
    chart = Chart("Test").candles(df).markers(entries, color="#00ff00", label="E")
    assert len(chart._markers) == 2


def test_chart_markers_list():
    df = _make_df()
    items = [
        {"time": "2024-01-03", "shape": "arrowUp", "position": "belowBar", "color": "#0f0", "label": "E"},
    ]
    chart = Chart("Test").candles(df).markers(items)
    assert len(chart._markers) == 1


def test_chart_candle_colors_bool():
    df = _make_df()
    mask = pd.Series(False, index=df.index)
    mask.iloc[0] = True
    chart = Chart("Test").candles(df).candle_colors(mask, color="#ff0000")
    bar = chart._candle_def.data[0]
    assert bar.get("color") == "#ff0000"


def test_chart_candle_colors_series():
    df = _make_df()
    colors = pd.Series(index=df.index, dtype=object)
    colors.iloc[1] = "#00ff00"
    chart = Chart("Test").candles(df).candle_colors(colors)
    assert chart._candle_def.data[1].get("color") == "#00ff00"
    assert "color" not in chart._candle_def.data[0]


def test_chart_volume_overlay():
    df = _make_df()
    chart = Chart("Test").candles(df).volume(df, position="overlay")
    assert len(chart._overlays) == 1
    assert chart._overlays[0].to_dict()["options"]["priceScaleId"] == "volume"


def test_chart_volume_pane():
    df = _make_df()
    chart = Chart("Test").candles(df).volume(df, position="pane")
    assert len(chart._subplots) == 1
    assert chart._subplots[0].label == "Volume"


def test_chart_repr_html_contains_iframe():
    df = _make_df()
    chart = Chart("Test", offline=False).candles(df)
    html = chart._repr_html_()
    assert "iframe" in html


def test_chart_no_candles_builds_config():
    chart = Chart("Empty")
    config = _build_config(chart)
    assert config["mainPane"]["candles"] == []
