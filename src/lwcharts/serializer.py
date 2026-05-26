import warnings
from datetime import datetime, date
from typing import Any

import pandas as pd


def _to_tv_time(ts: Any) -> str | int:
    if isinstance(ts, str):
        return ts
    if isinstance(ts, (int, float)):
        return int(ts)
    if isinstance(ts, date) and not isinstance(ts, datetime):
        return ts.strftime("%Y-%m-%d")
    if isinstance(ts, (pd.Timestamp, datetime)):
        if ts.hour == 0 and ts.minute == 0 and ts.second == 0:
            return ts.strftime("%Y-%m-%d")
        return int(ts.timestamp())
    return str(ts)


def df_to_ohlcv(
    df: pd.DataFrame,
    open_col: str,
    high_col: str,
    low_col: str,
    close_col: str,
    time_col: str | None,
    color_series: pd.Series | None = None,
    apply_color_to: str = "body",
) -> list[dict]:
    df = df.sort_index()
    mask = df[[open_col, high_col, low_col, close_col]].notna().all(axis=1)
    df = df[mask]

    result = []
    for idx, row in df.iterrows():
        time_val = _to_tv_time(row[time_col] if time_col else idx)
        d: dict = {
            "time": time_val,
            "open": float(row[open_col]),
            "high": float(row[high_col]),
            "low": float(row[low_col]),
            "close": float(row[close_col]),
        }
        if color_series is not None:
            raw = color_series.get(idx)
            if raw is not None and pd.notna(raw) and raw != "":
                if apply_color_to in ("body", "both"):
                    d["color"] = raw
                    d["borderColor"] = raw
                if apply_color_to in ("wick", "both"):
                    d["wickColor"] = raw
        result.append(d)
    return result


def _apply_fill_method(
    s: pd.Series,
    fill_method: str | None,
    candle_index: pd.Index | None,
    stacklevel: int = 3,
) -> pd.Series:
    if fill_method is None or candle_index is None:
        return s
    if fill_method == "ffill" and len(s) < 0.5 * len(candle_index):
        warnings.warn(
            f"Series '{s.name}' covers only {len(s) / len(candle_index):.0%} of candle index. "
            f"Using fill_method=None to avoid unintended forward-fill propagation. "
            f"Pass fill_method='ffill' explicitly to suppress this warning.",
            UserWarning,
            stacklevel=stacklevel,
        )
        return s
    return s.reindex(candle_index, method=fill_method)


def series_to_line(
    s: pd.Series,
    fill_method: str | None = None,
    candle_index: pd.Index | None = None,
    colors: list[str] | None = None,
) -> list[dict]:
    s = _apply_fill_method(s, fill_method, candle_index, stacklevel=4)
    s = s.sort_index()

    result = []
    for i, (idx, val) in enumerate(s.items()):
        if pd.isna(val):
            continue
        d: dict = {"time": _to_tv_time(idx), "value": float(val)}
        if colors is not None and i < len(colors):
            d["color"] = colors[i]
        result.append(d)
    return result


def histogram_colors(
    s: pd.Series,
    color_up: str,
    color_down: str,
    color_neutral: str = "rgba(139,148,158,0.5)",
) -> list[str]:
    result = []
    for val in s:
        if pd.isna(val) or val == 0:
            result.append(color_neutral)
        elif val > 0:
            result.append(color_up)
        else:
            result.append(color_down)
    return result


def detect_ohlc_cols(df: pd.DataFrame) -> tuple[str, str, str, str]:
    cols_lower = {c.lower(): c for c in df.columns}
    open_col = cols_lower.get("open") or cols_lower.get("o")
    high_col = cols_lower.get("high") or cols_lower.get("h")
    low_col = cols_lower.get("low") or cols_lower.get("l")
    close_col = cols_lower.get("close") or cols_lower.get("c")
    if not all([open_col, high_col, low_col, close_col]):
        raise ValueError(
            "Could not auto-detect OHLC columns. "
            "Pass explicit column names: open=, high=, low=, close="
        )
    return open_col, high_col, low_col, close_col  # type: ignore[return-value]


def _series_to_zones(series: pd.Series, palette: dict) -> list[dict]:
    """Convertit une Series catégorielle en liste de zones {from, to, color}.
    Les segments contigus de même label sont fusionnés.
    Labels absents du palette (y compris NaN) → ignorés.
    """
    zones = []
    current_label = None
    start_time = None

    for ts, label in series.items():
        try:
            is_na = pd.isna(label)
        except (TypeError, ValueError):
            is_na = False
        label_key = None if is_na else label

        if label_key != current_label:
            if current_label is not None and current_label in palette:
                zones.append({
                    "from": _to_tv_time(start_time),
                    "to": _to_tv_time(ts),
                    "color": palette[current_label],
                })
            current_label = label_key
            start_time = ts

    if current_label is not None and current_label in palette:
        zones.append({
            "from": _to_tv_time(start_time),
            "to": _to_tv_time(series.index[-1]),
            "color": palette[current_label],
        })

    return zones
