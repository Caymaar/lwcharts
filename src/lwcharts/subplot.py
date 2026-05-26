from __future__ import annotations

import warnings

import pandas as pd

from .annotations import HLineDef
from .serializer import (
    _apply_fill_method,
    _series_to_zones,
    _to_tv_time,
    detect_ohlc_cols,
    df_to_ohlcv,
    histogram_colors,
    series_to_line,
)
from .series import (
    _DARK_SERIES_COLORS,
    AreaDef,
    BaselineDef,
    HistogramDef,
    LineDef,
    SubplotCandleDef,
)


_VALID_Y_FORMATS = {None, "percent", "currency", "bps", "volume"}


class Subplot:
    def __init__(
        self,
        height_ratio: float = 0.2,
        label: str | None = None,
        y_min: float | None = None,
        y_max: float | None = None,
        y_format: str | None = None,
    ) -> None:
        self.height_ratio = height_ratio
        self.label = label
        self.y_format = y_format

        if (y_min is None) != (y_max is None):
            warnings.warn(
                f"y_min and y_max must both be set or both be None. "
                f"Ignoring {'y_max=' + str(y_max) if y_min is None else 'y_min=' + str(y_min)} "
                f"and falling back to autoscale.",
                UserWarning,
                stacklevel=2,
            )
            y_min = None
            y_max = None

        self.y_min = y_min
        self.y_max = y_max
        self._series: list = []
        self._hlines: list[HLineDef] = []
        self._bg_zones: list[dict] = []
        self._candle_index: pd.Index | None = None
        self._color_counter = 0

    def _next_color(self) -> str:
        color = _DARK_SERIES_COLORS[self._color_counter % len(_DARK_SERIES_COLORS)]
        self._color_counter += 1
        return color

    def _get_series(self, series: pd.Series | pd.DataFrame, col: str | None) -> pd.Series:
        if isinstance(series, pd.DataFrame):
            if col is None:
                raise ValueError("col is required when series is a DataFrame")
            return series[col]
        return series

    # ── candlestick (multi-timeframe) ─────────────────────────────────────────

    def candles(
        self,
        df: pd.DataFrame,
        open: str | None = None,  # noqa: A002
        high: str | None = None,
        low: str | None = None,
        close: str | None = None,
        time: str | None = None,
        style: str = "classic",
        up_color: str = "#26a641",
        down_color: str = "#f85149",
    ) -> "Subplot":
        if open is None:
            open_col, high_col, low_col, close_col = detect_ohlc_cols(df)
        else:
            open_col, high_col, low_col, close_col = open, high, low, close  # type: ignore

        data = df_to_ohlcv(df, open_col, high_col, low_col, close_col, time)
        # Insert at position 0 so it is the anchor for hlines and bgZones
        self._series.insert(
            0,
            SubplotCandleDef(data=data, style=style, up_color=up_color, down_color=down_color),
        )
        return self

    # alias used in some examples
    candle = candles

    # ── standard series ───────────────────────────────────────────────────────

    def line(
        self,
        series: pd.Series | pd.DataFrame,
        col: str | None = None,
        name: str | None = None,
        color: str | None = None,
        width: int = 1,
        style: str = "solid",
        fill_method: str | None = "ffill",
    ) -> "Subplot":
        s = self._get_series(series, col)
        name = name or getattr(s, "name", None) or "line"
        color = color or self._next_color()
        data = series_to_line(s, fill_method=fill_method, candle_index=self._candle_index)
        self._series.append(LineDef(data=data, name=name, color=color, width=width, style=style))
        return self

    def histogram(
        self,
        series: pd.Series | pd.DataFrame,
        col: str | None = None,
        name: str | None = None,
        color: str | None = None,
        color_up: str | None = None,
        color_down: str | None = None,
        fill_method: str | None = "ffill",
    ) -> "Subplot":
        s = self._get_series(series, col)
        name = name or getattr(s, "name", None) or "histogram"

        if color_up is not None or color_down is not None:
            s = _apply_fill_method(s, fill_method, self._candle_index, stacklevel=3)
            colors = histogram_colors(
                s,
                color_up=color_up or "#26a641",
                color_down=color_down or "#f85149",
            )
            data = series_to_line(s, fill_method=None, colors=colors)
            self._series.append(HistogramDef(data=data, name=name, color=None))
        else:
            if color is None:
                color = self._next_color()
            data = series_to_line(s, fill_method=fill_method, candle_index=self._candle_index)
            self._series.append(HistogramDef(data=data, name=name, color=color))
        return self

    def area(
        self,
        series: pd.Series | pd.DataFrame,
        col: str | None = None,
        name: str | None = None,
        top_color: str | None = None,
        bottom_color: str | None = None,
        line_color: str | None = None,
        fill_method: str | None = "ffill",
    ) -> "Subplot":
        s = self._get_series(series, col)
        name = name or getattr(s, "name", None) or "area"
        if line_color is None:
            line_color = self._next_color()
        data = series_to_line(s, fill_method=fill_method, candle_index=self._candle_index)
        self._series.append(
            AreaDef(data=data, name=name, top_color=top_color, bottom_color=bottom_color, line_color=line_color)
        )
        return self

    def baseline(
        self,
        series: pd.Series | pd.DataFrame,
        col: str | None = None,
        name: str | None = None,
        base: float = 0.0,
        top_line_color: str = "rgba(38,166,154,1)",
        top_fill_color1: str = "rgba(38,166,154,0.28)",
        top_fill_color2: str = "rgba(38,166,154,0.05)",
        bottom_line_color: str = "rgba(239,83,80,1)",
        bottom_fill_color1: str = "rgba(239,83,80,0.05)",
        bottom_fill_color2: str = "rgba(239,83,80,0.28)",
        fill_method: str | None = "ffill",
    ) -> "Subplot":
        s = self._get_series(series, col)
        name = name or getattr(s, "name", None) or "baseline"
        data = series_to_line(s, fill_method=fill_method, candle_index=self._candle_index)
        self._series.append(
            BaselineDef(
                data=data, name=name, base=base,
                top_line_color=top_line_color, top_fill_color1=top_fill_color1,
                top_fill_color2=top_fill_color2, bottom_line_color=bottom_line_color,
                bottom_fill_color1=bottom_fill_color1, bottom_fill_color2=bottom_fill_color2,
            )
        )
        return self

    def hline(
        self,
        price: float,
        color: str | None = None,
        style: str = "dashed",
        width: int = 1,
        label: str | None = None,
    ) -> "Subplot":
        self._hlines.append(
            HLineDef(
                price=float(price),
                color=color or "rgba(139,148,158,0.5)",
                style=style,
                width=width,
                label=label or "",
                axis_label_visible=label is not None,
            )
        )
        return self

    # ── background zones ──────────────────────────────────────────────────────

    def bg_zone(self, time_from, time_to, color: str) -> "Subplot":
        self._bg_zones.append({
            "from": _to_tv_time(time_from),
            "to": _to_tv_time(time_to),
            "color": color,
        })
        return self

    def bg_zones(self, items) -> "Subplot":
        if isinstance(items, pd.DataFrame):
            for _, row in items.iterrows():
                self._bg_zones.append({
                    "from": _to_tv_time(row["from"]),
                    "to": _to_tv_time(row["to"]),
                    "color": row["color"],
                })
        else:
            for item in items:
                self._bg_zones.append({
                    "from": _to_tv_time(item["from"]),
                    "to": _to_tv_time(item["to"]),
                    "color": item["color"],
                })
        return self

    def bg_zones_from_series(self, series: pd.Series, palette: dict) -> "Subplot":
        self._bg_zones.extend(_series_to_zones(series, palette))
        return self

    def bg_zones_from_mask(
        self,
        mask: pd.Series,
        color_true: str,
        color_false: str | None = None,
    ) -> "Subplot":
        palette: dict = {True: color_true}
        if color_false is not None:
            palette[False] = color_false
        return self.bg_zones_from_series(mask, palette)
