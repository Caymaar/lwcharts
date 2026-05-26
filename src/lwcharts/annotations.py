from dataclasses import dataclass
from typing import Literal

from .series import LineStyle, _LINE_STYLE_MAP


@dataclass
class MarkerDef:
    time: str | int
    shape: Literal["arrowUp", "arrowDown", "circle", "square"] = "circle"
    position: Literal["aboveBar", "belowBar", "inBar"] = "aboveBar"
    color: str = "#ffffff"
    label: str = ""

    def to_dict(self) -> dict:
        return {
            "time": self.time,
            "shape": self.shape,
            "position": self.position,
            "color": self.color,
            "text": self.label,
        }


@dataclass
class HLineDef:
    price: float
    color: str = "rgba(139,148,158,0.5)"
    style: LineStyle = "dashed"
    width: int = 1
    label: str = ""
    axis_label_visible: bool = True

    def to_dict(self) -> dict:
        return {
            "price": self.price,
            "color": self.color,
            "lineWidth": self.width,
            "lineStyle": _LINE_STYLE_MAP[self.style],
            "axisLabelVisible": self.axis_label_visible,
            "title": self.label,
        }


@dataclass
class CandleColorDef:
    colors: dict[str | int, str]
    apply_to: Literal["body", "wick", "both"] = "body"
