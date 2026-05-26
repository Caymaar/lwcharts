import pandas as pd
import pytest
from lwcharts.serializer import (
    _to_tv_time,
    df_to_ohlcv,
    histogram_colors,
    series_to_line,
)


def test_to_tv_time_date_string():
    assert _to_tv_time("2024-01-01") == "2024-01-01"


def test_to_tv_time_timestamp_midnight():
    ts = pd.Timestamp("2024-01-15")
    assert _to_tv_time(ts) == "2024-01-15"


def test_to_tv_time_timestamp_intraday():
    ts = pd.Timestamp("2024-01-15 09:30:00")
    result = _to_tv_time(ts)
    assert isinstance(result, int)
    assert result > 0


def test_to_tv_time_int():
    assert _to_tv_time(1700000000) == 1700000000


def test_df_to_ohlcv_basic():
    idx = pd.date_range("2024-01-01", periods=3, freq="B")
    df = pd.DataFrame(
        {"open": [1.0, 2.0, 3.0], "high": [1.5, 2.5, 3.5],
         "low": [0.5, 1.5, 2.5], "close": [1.2, 2.2, 3.2]},
        index=idx,
    )
    result = df_to_ohlcv(df, "open", "high", "low", "close", None)
    assert len(result) == 3
    assert result[0]["open"] == 1.0
    assert result[0]["close"] == 1.2
    assert "time" in result[0]


def test_df_to_ohlcv_drops_nan():
    idx = pd.date_range("2024-01-01", periods=3, freq="B")
    df = pd.DataFrame(
        {"open": [1.0, None, 3.0], "high": [1.5, 2.5, 3.5],
         "low": [0.5, 1.5, 2.5], "close": [1.2, 2.2, 3.2]},
        index=idx,
    )
    result = df_to_ohlcv(df, "open", "high", "low", "close", None)
    assert len(result) == 2


def test_df_to_ohlcv_with_colors_body():
    idx = pd.date_range("2024-01-01", periods=2, freq="B")
    df = pd.DataFrame(
        {"open": [1.0, 2.0], "high": [1.5, 2.5], "low": [0.5, 1.5], "close": [1.2, 2.2]},
        index=idx,
    )
    colors = pd.Series(["#ff0000", None], index=idx)
    result = df_to_ohlcv(df, "open", "high", "low", "close", None, color_series=colors)
    assert result[0]["color"] == "#ff0000"
    assert "color" not in result[1]


def test_series_to_line_basic():
    idx = pd.date_range("2024-01-01", periods=3, freq="B")
    s = pd.Series([10.0, 20.0, 30.0], index=idx)
    result = series_to_line(s)
    assert len(result) == 3
    assert result[0]["value"] == 10.0


def test_series_to_line_drops_nan():
    idx = pd.date_range("2024-01-01", periods=3, freq="B")
    s = pd.Series([10.0, float("nan"), 30.0], index=idx)
    result = series_to_line(s)
    assert len(result) == 2


def test_series_to_line_ffill():
    candle_idx = pd.date_range("2024-01-01", periods=5, freq="B")
    series_idx = candle_idx[::2]  # every other day
    s = pd.Series([1.0, 2.0, 3.0], index=series_idx)
    result = series_to_line(s, fill_method="ffill", candle_index=candle_idx)
    assert len(result) == 5


def test_series_to_line_ffill_warning_low_coverage():
    candle_idx = pd.date_range("2024-01-01", periods=20, freq="B")
    s = pd.Series([1.0, 2.0], index=candle_idx[:2], name="test")
    with pytest.warns(UserWarning, match="covers only"):
        result = series_to_line(s, fill_method="ffill", candle_index=candle_idx)
    assert len(result) == 2  # no fill happened


def test_histogram_colors():
    s = pd.Series([1.0, -1.0, 0.0])
    result = histogram_colors(s, color_up="#green", color_down="#red")
    assert result[0] == "#green"
    assert result[1] == "#red"
    assert result[2] == "rgba(139,148,158,0.5)"
