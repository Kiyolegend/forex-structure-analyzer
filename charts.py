"""
forex/charts.py
---------------
Chart generation using Plotly.
Renders OHLC candlestick charts with market structure annotations
(HH, HL, LH, LL) and BOS markers.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


# Color scheme for structure labels
COLORS = {
    "HH": "#26a69a",   # teal / bullish
    "HL": "#80cbc4",   # light teal / bullish
    "LH": "#ef5350",   # red / bearish
    "LL": "#ff8a80",   # light red / bearish
    "SH": "#b0bec5",   # grey / first swing
    "SL": "#b0bec5",   # grey / first swing
    "BOS_UP": "#26a69a",
    "BOS_DOWN": "#ef5350",
}

LABEL_COLORS = {
    "HH": "green",
    "HL": "lightgreen",
    "LH": "red",
    "LL": "salmon",
    "SH": "grey",
    "SL": "grey",
}


def build_candlestick_chart(
    df: pd.DataFrame,
    structure_points: list,
    bos_events: list,
    title: str = "Market Structure",
) -> go.Figure:
    """
    Build an interactive Plotly candlestick chart with structure labels.

    Args:
        df:               OHLC DataFrame with 'datetime', 'open', 'high', 'low', 'close'
        structure_points: List of structure dicts (from classify_structure)
        bos_events:       List of BOS event dicts
        title:            Chart title string

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # --- Candlestick trace ---
    fig.add_trace(
        go.Candlestick(
            x=df["datetime"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Price",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        )
    )

    # --- Structure point annotations ---
    for point in structure_points:
        label = point["type"]
        price = point["price"]
        dt = point["datetime"]
        is_high = point["is_high"]

        color = LABEL_COLORS.get(label, "grey")

        # Place label above high points, below low points
        y_anchor = "bottom" if is_high else "top"
        y_shift = 6 if is_high else -6

        fig.add_annotation(
            x=dt,
            y=price,
            text=f"<b>{label}</b>",
            showarrow=True,
            arrowhead=2,
            arrowsize=0.8,
            arrowcolor=color,
            font=dict(size=10, color=color),
            ay=y_shift * (-10),
            ax=0,
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor=color,
            borderwidth=1,
        )

    # --- Connect structure points with lines ---
    highs = [p for p in structure_points if p["is_high"]]
    lows = [p for p in structure_points if not p["is_high"]]

    if len(highs) >= 2:
        fig.add_trace(
            go.Scatter(
                x=[p["datetime"] for p in highs],
                y=[p["price"] for p in highs],
                mode="lines+markers",
                line=dict(color="#ef5350", width=1, dash="dot"),
                marker=dict(size=5, color="#ef5350"),
                name="Swing Highs",
                opacity=0.7,
            )
        )

    if len(lows) >= 2:
        fig.add_trace(
            go.Scatter(
                x=[p["datetime"] for p in lows],
                y=[p["price"] for p in lows],
                mode="lines+markers",
                line=dict(color="#26a69a", width=1, dash="dot"),
                marker=dict(size=5, color="#26a69a"),
                name="Swing Lows",
                opacity=0.7,
            )
        )

    # --- BOS markers ---
    for bos in bos_events:
        bos_color = "#26a69a" if bos["type"] == "BOS_UP" else "#ef5350"
        label = "BOS ↑" if bos["type"] == "BOS_UP" else "BOS ↓"
        fig.add_annotation(
            x=bos["datetime"],
            y=bos["price"],
            text=f"<b>{label}</b>",
            showarrow=False,
            font=dict(size=11, color=bos_color),
            bgcolor="rgba(0,0,0,0.6)",
            bordercolor=bos_color,
            borderwidth=1.5,
        )

    # --- Layout ---
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
    )

    return fig
