from __future__ import annotations

import base64
import json
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Timer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chart import Chart
    from .layout import Dashboard

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_VENDOR_JS_PATH = (
    Path(__file__).parent / "vendor" / "lightweight-charts.standalone.production.js"
)
_CDN_URL = (
    "https://unpkg.com/lightweight-charts@5.2.0"
    "/dist/lightweight-charts.standalone.production.js"
)


def _js_tag(offline: bool) -> str:
    if offline:
        if not _VENDOR_JS_PATH.exists():
            raise FileNotFoundError(
                f"lwcharts vendor JS not found at {_VENDOR_JS_PATH}.\n"
                f"Run:  uv run python scripts/update_vendor.py\n"
                f"Or use Chart(..., offline=False) to load from CDN."
            )
        js = _VENDOR_JS_PATH.read_text(encoding="utf-8")
        return f"<script>\n{js}\n</script>"
    return f'<script src="{_CDN_URL}"></script>'


def _build_config(chart: "Chart") -> dict:
    total_h = chart.height
    sub_ratio_sum = sum(sp.height_ratio for sp in chart._subplots)
    main_ratio = max(1 - sub_ratio_sum, 0.35)
    main_h = int(total_h * main_ratio)

    return {
        "title": chart.title,
        "theme": chart.theme,
        "totalHeight": total_h,
        "mainPaneHeight": main_h,
        "candleStyle": chart.candle_style,
        "mainPane": {
            "candles": chart._candle_def.data if chart._candle_def else [],
            "overlays": [s.to_dict() for s in chart._overlays],
            "hlines": [h.to_dict() for h in chart._hlines],
            "markers": [m.to_dict() for m in chart._markers],
            "bgZones": chart._bg_zones,
            "yFormat": chart.y_format,
        },
        "subPanes": [
            {
                "label": sp.label or "",
                "heightPx": int(total_h * sp.height_ratio),
                "yMin": sp.y_min,
                "yMax": sp.y_max,
                "yFormat": sp.y_format,
                "series": [s.to_dict() for s in sp._series],
                "hlines": [h.to_dict() for h in sp._hlines],
                "bgZones": sp._bg_zones,
            }
            for sp in chart._subplots
        ],
    }


def _render_html(chart: "Chart") -> str:
    template = (_TEMPLATES_DIR / "chart.html").read_text("utf-8")
    config_json = json.dumps(_build_config(chart), default=str, ensure_ascii=False)
    html = template.replace("__LW_SCRIPT__", _js_tag(chart.offline))
    html = html.replace("__CHART_CONFIG__", config_json)
    return html


def _render_html_dashboard(dashboard: "Dashboard") -> str:
    template = (_TEMPLATES_DIR / "dashboard.html").read_text("utf-8")

    # propagate offline + theme from dashboard to each chart
    for chart in dashboard._charts:
        chart.offline = dashboard.offline
        if dashboard.theme:
            chart.theme = dashboard.theme
        if dashboard.row_height:
            chart.height = dashboard.row_height

    configs = [_build_config(c) for c in dashboard._charts]
    config_json = json.dumps(configs, default=str, ensure_ascii=False)

    html = template.replace("__LW_SCRIPT__", _js_tag(dashboard.offline))
    html = html.replace("__DASHBOARD_CONFIG__", config_json)
    html = html.replace("__COLS__", str(dashboard.cols))
    html = html.replace("__TITLE__", dashboard.title)
    html = html.replace("__THEME__", dashboard.theme or "dark")
    return html


def repr_html_chart(chart: "Chart") -> str:
    html = _render_html(chart)
    encoded = base64.b64encode(html.encode("utf-8")).decode("ascii")
    height = chart.height + 70
    return (
        f'<iframe src="data:text/html;base64,{encoded}" '
        f'width="100%" height="{height}px" frameborder="0" '
        f'style="border:none;display:block;"></iframe>'
    )


def repr_html_dashboard(dashboard: "Dashboard") -> str:
    html = _render_html_dashboard(dashboard)
    encoded = base64.b64encode(html.encode("utf-8")).decode("ascii")
    import math
    rows = math.ceil(len(dashboard._charts) / max(dashboard.cols, 1))
    height = (dashboard.row_height or 500) * rows + 80
    return (
        f'<iframe src="data:text/html;base64,{encoded}" '
        f'width="100%" height="{height}px" frameborder="0" '
        f'style="border:none;display:block;"></iframe>'
    )


def show(chart: "Chart") -> None:
    html = _render_html(chart)
    with tempfile.NamedTemporaryFile(
        suffix=".html", delete=False, mode="w", encoding="utf-8"
    ) as f:
        f.write(html)
        path = f.name
    webbrowser.open(f"file://{path}")


def serve_chart(chart: "Chart", port: int = 8080, open_browser: bool = True) -> None:
    html = _render_html(chart)
    _serve_html(html, port, open_browser)


def serve_dashboard(
    dashboard: "Dashboard", port: int = 8080, open_browser: bool = True
) -> None:
    html = _render_html_dashboard(dashboard)
    _serve_html(html, port, open_browser)


def _serve_html(html: str, port: int, open_browser: bool) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        def log_message(self, format, *args):  # noqa: A002
            pass

    try:
        server = HTTPServer(("localhost", port), Handler)
    except OSError:
        raise OSError(
            f"Port {port} is already in use. "
            f"Try: chart.serve(port=8081)"
        )

    print(f"Serving at http://localhost:{port} — Ctrl-C to stop")
    if open_browser:
        Timer(0.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def to_html(chart: "Chart", path) -> None:
    Path(path).write_text(_render_html(chart), encoding="utf-8")


def to_html_dashboard(dashboard: "Dashboard", path) -> None:
    Path(path).write_text(_render_html_dashboard(dashboard), encoding="utf-8")
