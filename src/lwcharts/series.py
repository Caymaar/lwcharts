from dataclasses import dataclass
from typing import Literal

LineStyle = Literal["solid", "dashed", "dotted", "large_dashed", "sparse_dotted"]

_LINE_STYLE_MAP: dict[str, int] = {
    "solid": 0,
    "dashed": 1,
    "dotted": 2,
    "large_dashed": 3,
    "sparse_dotted": 4,
}

_DARK_SERIES_COLORS = [
    "#58a6ff",
    "#f0b429",
    "#a5b4fc",
    "#26a641",
    "#f85149",
    "#c084fc",
    "#fb923c",
    "#e879f9",
]


@dataclass
class LineDef:
    data: list[dict]
    name: str = "line"
    color: str | None = None
    width: int = 1
    style: LineStyle = "solid"
    price_scale_id: str = "right"
    last_value_visible: bool = False
    price_line_visible: bool = False

    def to_dict(self) -> dict:
        opts: dict = {
            "lineWidth": self.width,
            "lineStyle": _LINE_STYLE_MAP[self.style],
            "priceScaleId": self.price_scale_id,
            "lastValueVisible": self.last_value_visible,
            "priceLineVisible": self.price_line_visible,
        }
        if self.color is not None:
            opts["color"] = self.color
        return {"type": "line", "name": self.name, "data": self.data, "options": opts}


@dataclass
class HistogramDef:
    data: list[dict]
    name: str = "histogram"
    color: str | None = None
    price_scale_id: str = "right"
    last_value_visible: bool = False
    price_line_visible: bool = False

    def to_dict(self) -> dict:
        opts: dict = {
            "priceScaleId": self.price_scale_id,
            "lastValueVisible": self.last_value_visible,
            "priceLineVisible": self.price_line_visible,
        }
        if self.color is not None:
            opts["color"] = self.color
        return {"type": "histogram", "name": self.name, "data": self.data, "options": opts}


@dataclass
class AreaDef:
    data: list[dict]
    name: str = "area"
    top_color: str | None = None
    bottom_color: str | None = None
    line_color: str | None = None
    price_scale_id: str = "right"
    last_value_visible: bool = False
    price_line_visible: bool = False

    def to_dict(self) -> dict:
        opts: dict = {
            "priceScaleId": self.price_scale_id,
            "lastValueVisible": self.last_value_visible,
            "priceLineVisible": self.price_line_visible,
        }
        if self.top_color is not None:
            opts["topColor"] = self.top_color
        if self.bottom_color is not None:
            opts["bottomColor"] = self.bottom_color
        if self.line_color is not None:
            opts["lineColor"] = self.line_color
        return {"type": "area", "name": self.name, "data": self.data, "options": opts}


@dataclass
class BaselineDef:
    data: list[dict]
    name: str = "baseline"
    base: float = 0.0
    top_line_color: str = "rgba(38,166,154,1)"
    top_fill_color1: str = "rgba(38,166,154,0.28)"
    top_fill_color2: str = "rgba(38,166,154,0.05)"
    bottom_line_color: str = "rgba(239,83,80,1)"
    bottom_fill_color1: str = "rgba(239,83,80,0.05)"
    bottom_fill_color2: str = "rgba(239,83,80,0.28)"
    price_scale_id: str = "right"
    last_value_visible: bool = False
    price_line_visible: bool = False

    def to_dict(self) -> dict:
        opts: dict = {
            "baseValue": {"type": "price", "price": self.base},
            "topLineColor": self.top_line_color,
            "topFillColor1": self.top_fill_color1,
            "topFillColor2": self.top_fill_color2,
            "bottomLineColor": self.bottom_line_color,
            "bottomFillColor1": self.bottom_fill_color1,
            "bottomFillColor2": self.bottom_fill_color2,
            "priceScaleId": self.price_scale_id,
            "lastValueVisible": self.last_value_visible,
            "priceLineVisible": self.price_line_visible,
        }
        return {"type": "baseline", "name": self.name, "data": self.data, "options": opts}


@dataclass
class CandleDef:
    data: list[dict]
    style: Literal["classic", "hollow", "bars"] = "classic"

    def to_dict(self) -> dict:
        return {"style": self.style, "data": self.data}


@dataclass
class SubplotCandleDef:
    """Série candlestick/bar pour un Subplot (multi-timeframe)."""
    data: list[dict]
    style: Literal["classic", "hollow", "bars"] = "classic"
    up_color: str = "#26a641"
    down_color: str = "#f85149"

    def to_dict(self) -> dict:
        if self.style == "hollow":
            opts = {
                "upColor": "transparent",
                "downColor": self.down_color,
                "borderVisible": True,
                "borderUpColor": self.up_color,
                "borderDownColor": self.down_color,
                "wickUpColor": self.up_color,
                "wickDownColor": self.down_color,
            }
            return {"type": "candlestick", "name": "Candles", "data": self.data, "options": opts}
        if self.style == "bars":
            return {
                "type": "bar",
                "name": "Candles",
                "data": self.data,
                "options": {"upColor": self.up_color, "downColor": self.down_color},
            }
        return {
            "type": "candlestick",
            "name": "Candles",
            "data": self.data,
            "options": {
                "upColor": self.up_color,
                "downColor": self.down_color,
                "borderVisible": False,
                "wickUpColor": self.up_color,
                "wickDownColor": self.down_color,
            },
        }


@dataclass
class VolumeOverlayDef:
    data: list[dict]
    up_color: str = "rgba(38,166,154,0.5)"
    down_color: str = "rgba(239,83,80,0.5)"

    def to_dict(self) -> dict:
        return {
            "type": "histogram",
            "name": "Volume",
            "data": self.data,
            "options": {
                "priceScaleId": "vol",
                "priceFormat": {"type": "volume"},
                # "scaleMargins": {"top": 0.25, "bottom": 0},
                # "lastValueVisible": False,
                # "priceLineVisible": False,
            },
        }
