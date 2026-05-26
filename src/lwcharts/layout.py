from __future__ import annotations

from pathlib import Path
from typing import Literal

from .chart import Chart


class Dashboard:
    def __init__(
        self,
        title: str = "Dashboard",
        cols: int = 2,
        row_height: int = 500,
        theme: Literal["dark", "light"] = "dark",
        offline: bool = True,
    ) -> None:
        self.title = title
        self.cols = cols
        self.row_height = row_height
        self.theme = theme
        self.offline = offline
        self._charts: list[Chart] = []

    def add(self, chart: Chart) -> "Dashboard":
        self._charts.append(chart)
        return self

    def serve(self, port: int = 1338, open_browser: bool = True) -> None:
        from . import renderer
        renderer.serve_dashboard(self, port=port, open_browser=open_browser)

    def to_html(self, path: str | Path) -> None:
        from . import renderer
        renderer.to_html_dashboard(self, path)

    def _repr_html_(self) -> str:
        from . import renderer
        return renderer.repr_html_dashboard(self)
