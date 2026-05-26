from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from .annotations import HLineDef, MarkerDef
from .serializer import _series_to_zones, _to_tv_time, detect_ohlc_cols, df_to_ohlcv, series_to_line
from .series import (
    _DARK_SERIES_COLORS,
    AreaDef,
    BaselineDef,
    CandleDef,
    HistogramDef,
    LineDef,
    VolumeOverlayDef,
)
from .subplot import Subplot


class Chart:
    def __init__(
        self,
        title: str = "",
        theme: Literal["dark", "light"] = "dark",
        height: int = 700,
        candle_style: Literal["classic", "hollow", "bars"] = "classic",
        offline: bool = True,
        y_format: str | None = None,
    ) -> None:
        self.title = title
        self.theme = theme
        self.height = height
        self.candle_style = candle_style
        self.offline = offline
        self.y_format = y_format

        self._candle_def: CandleDef | None = None
        self._candle_df: pd.DataFrame | None = None
        self._candle_cols: tuple | None = None
        self._candle_index: pd.Index | None = None

        self._overlays: list = []
        self._hlines: list[HLineDef] = []
        self._markers: list[MarkerDef] = []
        self._bg_zones: list[dict] = []
        self._subplots: list[Subplot] = []
        self._color_counter = 0

    def _next_color(self) -> str:
        color = _DARK_SERIES_COLORS[self._color_counter % len(_DARK_SERIES_COLORS)]
        self._color_counter += 1
        return color

    # ── candles ──────────────────────────────────────────────────────────────

    def candles(
        self,
        df: pd.DataFrame,
        open: str | None = None,  # noqa: A002
        high: str | None = None,
        low: str | None = None,
        close: str | None = None,
        time: str | None = None,
    ) -> "Chart":
        if open is None:
            open_col, high_col, low_col, close_col = detect_ohlc_cols(df)
        else:
            open_col, high_col, low_col, close_col = open, high, low, close  # type: ignore

        self._candle_df = df
        self._candle_cols = (open_col, high_col, low_col, close_col, time)
        self._candle_index = df.index

        data = df_to_ohlcv(df, open_col, high_col, low_col, close_col, time)
        self._candle_def = CandleDef(data=data, style=self.candle_style)

        for sp in self._subplots:
            sp._candle_index = self._candle_index

        return self

    def candle_colors(
        self,
        colors: pd.Series,
        color: str | None = None,
        apply_to: Literal["body", "wick", "both"] = "body",
    ) -> "Chart":
        if self._candle_def is None:
            raise ValueError("Call .candles() before .candle_colors()")

        if colors.dtype == bool:
            if color is None:
                raise ValueError("color is required when colors is a boolean Series")
            color_series: pd.Series = pd.Series(index=colors.index, dtype=object)
            color_series[colors] = color
        else:
            color_series = colors

        open_col, high_col, low_col, close_col, time_col = self._candle_cols  # type: ignore
        data = df_to_ohlcv(
            self._candle_df,  # type: ignore
            open_col,
            high_col,
            low_col,
            close_col,
            time_col,
            color_series=color_series,
            apply_color_to=apply_to,
        )
        self._candle_def = CandleDef(data=data, style=self.candle_style)
        return self

    # ── overlays ──────────────────────────────────────────────────────────────

    def line(
        self,
        series: pd.Series | pd.DataFrame,
        col: str | None = None,
        name: str | None = None,
        color: str | None = None,
        width: int = 1,
        style: str = "solid",
        fill_method: str | None = "ffill",
    ) -> "Chart":
        s = self._as_series(series, col)
        name = name or getattr(s, "name", None) or "line"
        color = color or self._next_color()
        data = series_to_line(s, fill_method=fill_method, candle_index=self._candle_index)
        self._overlays.append(LineDef(data=data, name=name, color=color, width=width, style=style))
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
    ) -> "Chart":
        s = self._as_series(series, col)
        name = name or getattr(s, "name", None) or "area"
        if line_color is None:
            line_color = self._next_color()
        data = series_to_line(s, fill_method=fill_method, candle_index=self._candle_index)
        self._overlays.append(
            AreaDef(
                data=data,
                name=name,
                top_color=top_color,
                bottom_color=bottom_color,
                line_color=line_color,
            )
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
    ) -> "Chart":
        s = self._as_series(series, col)
        name = name or getattr(s, "name", None) or "baseline"
        data = series_to_line(s, fill_method=fill_method, candle_index=self._candle_index)
        self._overlays.append(
            BaselineDef(
                data=data,
                name=name,
                base=base,
                top_line_color=top_line_color,
                top_fill_color1=top_fill_color1,
                top_fill_color2=top_fill_color2,
                bottom_line_color=bottom_line_color,
                bottom_fill_color1=bottom_fill_color1,
                bottom_fill_color2=bottom_fill_color2,
            )
        )
        return self

    def volume(
        self,
        df: pd.DataFrame,
        col: str = "volume",
        time: str | None = None,
        position: Literal["overlay", "pane"] = "overlay",
        up_color: str = "rgba(38,166,154,0.5)",
        down_color: str = "rgba(239,83,80,0.5)",
    ) -> "Chart":
        open_col = close_col = None
        try:
            open_col, _, _, close_col = detect_ohlc_cols(df)
        except ValueError:
            pass

        df_sorted = df.sort_index()
        data = []
        for idx, row in df_sorted.iterrows():
            if pd.isna(row[col]):
                continue
            bar_color = up_color
            if (
                open_col
                and close_col
                and not pd.isna(row[open_col])
                and not pd.isna(row[close_col])
            ):
                bar_color = up_color if row[close_col] >= row[open_col] else down_color
            time_val = _to_tv_time(row[time] if time else idx)
            data.append({"time": time_val, "value": float(row[col]), "color": bar_color})

        if position == "overlay":
            self._overlays.append(VolumeOverlayDef(data=data, up_color=up_color, down_color=down_color))
        else:
            vol_pane = Subplot(height_ratio=0.15, label="Volume")
            vol_pane._series.append(
                HistogramDef(data=data, name="Volume", price_scale_id="right")
            )
            if self._candle_index is not None:
                vol_pane._candle_index = self._candle_index
            self._subplots.insert(0, vol_pane)

        return self

    # ── annotations ───────────────────────────────────────────────────────────

    def hline(
        self,
        price: float,
        color: str | None = None,
        style: str = "dashed",
        width: int = 1,
        label: str | None = None,
    ) -> "Chart":
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

    def marker(
        self,
        time,
        shape: str = "arrowUp",
        position: str = "belowBar",
        color: str | None = None,
        label: str | None = None,
    ) -> "Chart":
        self._markers.append(
            MarkerDef(
                time=_to_tv_time(time),
                shape=shape,  # type: ignore
                position=position,  # type: ignore
                color=color or "#ffffff",
                label=label or "",
            )
        )
        return self

    def markers(
        self,
        items,
        shape: str = "arrowUp",
        position: str = "belowBar",
        color: str | None = None,
        label: str | None = None,
    ) -> "Chart":
        if isinstance(items, pd.Series) and items.dtype == bool:
            for ts, val in items.items():
                if val:
                    self._markers.append(
                        MarkerDef(
                            time=_to_tv_time(ts),
                            shape=shape,  # type: ignore
                            position=position,  # type: ignore
                            color=color or "#ffffff",
                            label=label or "",
                        )
                    )
        elif isinstance(items, pd.DataFrame):
            for _, row in items.iterrows():
                self._markers.append(
                    MarkerDef(
                        time=_to_tv_time(row["time"]),
                        shape=row.get("shape", shape),  # type: ignore
                        position=row.get("position", position),  # type: ignore
                        color=row.get("color", color or "#ffffff"),
                        label=row.get("label", label or ""),
                    )
                )
        elif isinstance(items, list):
            for item in items:
                self._markers.append(
                    MarkerDef(
                        time=_to_tv_time(item["time"]),
                        shape=item.get("shape", shape),  # type: ignore
                        position=item.get("position", position),  # type: ignore
                        color=item.get("color", color or "#ffffff"),
                        label=item.get("label", label or ""),
                    )
                )
        return self

    # ── background zones ──────────────────────────────────────────────────────

    def bg_zone(self, time_from, time_to, color: str) -> "Chart":
        self._bg_zones.append({
            "from": _to_tv_time(time_from),
            "to": _to_tv_time(time_to),
            "color": color,
        })
        return self

    def bg_zones(self, items) -> "Chart":
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

    def bg_zones_from_series(self, series: pd.Series, palette: dict) -> "Chart":
        self._bg_zones.extend(_series_to_zones(series, palette))
        return self

    def bg_zones_from_mask(
        self,
        mask: pd.Series,
        color_true: str,
        color_false: str | None = None,
    ) -> "Chart":
        palette: dict = {True: color_true}
        if color_false is not None:
            palette[False] = color_false
        return self.bg_zones_from_series(mask, palette)

    # ── subplots ──────────────────────────────────────────────────────────────

    def add_subplot(self, subplot: Subplot) -> "Chart":
        if self._candle_index is not None:
            subplot._candle_index = self._candle_index
        self._subplots.append(subplot)
        return self

    # ── rendering ─────────────────────────────────────────────────────────────

    def show(self) -> None:
        from . import renderer
        renderer.show(self)

    def serve(self, port: int = 1338, open_browser: bool = True) -> None:
        from . import renderer
        renderer.serve_chart(self, port=port, open_browser=open_browser)

    def to_html(self, path: str | Path) -> None:
        from . import renderer
        renderer.to_html(self, path)

    def _repr_html_(self) -> str:
        from . import renderer
        return renderer.repr_html_chart(self)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _as_series(
        self, series: pd.Series | pd.DataFrame, col: str | None
    ) -> pd.Series:
        if isinstance(series, pd.DataFrame):
            if col is None:
                raise ValueError("col is required when series is a DataFrame")
            return series[col]
        return series
