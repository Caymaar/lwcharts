"""Dashboard 2x2 multi-actifs."""
import pandas as pd
from lwcharts import Chart, Dashboard, Subplot


def make_chart(ticker: str) -> Chart:

    df = pd.read_parquet(f"examples/data/{ticker}.parquet")
    ema = df["close"].ewm(span=20).mean()
    delta = df["close"].diff()
    gain = delta.clip(lower=0).ewm(com=13).mean()
    loss = (-delta.clip(upper=0)).ewm(com=13).mean()
    rsi = 100 - 100 / (1 + gain / loss)

    return (
        Chart(title=ticker, theme="dark", height=400)
        .candles(df)
        .line(ema, color="#f0b429")
        .volume(df)
        .add_subplot(
            Subplot(height_ratio=0.25, label="RSI", y_min=0, y_max=100)
            .line(rsi, color="#58a6ff")
            .hline(70, style="dashed")
            .hline(30, style="dashed")
        )
    )


dash = (
    Dashboard(title="Equity Dashboard", cols=2, row_height=450)
    .add(make_chart("ZQK.US"))
    .add(make_chart("ZS.US"))
    .add(make_chart("ZTS.US"))
    .add(make_chart("ZU.US"))
)

dash.serve()
