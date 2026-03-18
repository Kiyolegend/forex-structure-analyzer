"""
app.py
------
Forex Trading Analysis Application — Streamlit UI

This is the main entry point. It:
  1. Lets the user choose a currency pair and pair of timeframes to view
  2. Fetches live OHLC candle data via Twelve Data
  3. Runs market structure analysis (HH, HL, LH, LL, BOS)
  4. Shows multi-timeframe bias and a trade idea
  5. Renders interactive candlestick charts with structure labels
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from forex.data import fetch_multi_timeframe, SUPPORTED_PAIRS
from forex.analysis import get_multi_timeframe_bias, get_key_levels
from forex.charts import build_candlestick_chart


# ──────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Forex Structure Analyzer",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Forex Market Structure Analyzer")
st.caption(
    "Live OHLC data from Twelve Data · Structure-based trade bias (HH / HL / LH / LL)"
)

# ──────────────────────────────────────────────
# Sidebar — controls
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")

    pair = st.selectbox(
        "Currency Pair",
        options=SUPPORTED_PAIRS,
        index=0,
        help="Select the forex pair to analyze.",
    )

    st.markdown("---")
    st.markdown("**Timeframes fetched:**")
    st.markdown("- **4H** — sets the higher-timeframe bias")
    st.markdown("- **1H** — confirms the bias")
    st.markdown("- **5M** — entry-level analysis")

    st.markdown("---")

    chart_tf = st.selectbox(
        "Chart to display",
        options=["5min", "1h", "4h"],
        index=0,
        help="Which timeframe chart to show below.",
    )

    run_btn = st.button("🔄 Fetch & Analyze", use_container_width=True)

    st.markdown("---")
    st.caption(
        "Data provided by [Twelve Data](https://twelvedata.com). "
        "Free tier: ~800 req/day."
    )


# ──────────────────────────────────────────────
# Helper — color for bias
# ──────────────────────────────────────────────
def bias_color(bias: str) -> str:
    if bias in ("bullish", "BUY"):
        return "🟢"
    elif bias in ("bearish", "SELL"):
        return "🔴"
    return "🟡"


def trend_badge(trend: str) -> str:
    colors = {
        "bullish": "green",
        "bearish": "red",
        "consolidation": "orange",
        "neutral": "gray",
    }
    icons = {
        "bullish": "▲ BULLISH",
        "bearish": "▼ BEARISH",
        "consolidation": "↔ CONSOLIDATION",
        "neutral": "— NEUTRAL",
    }
    return icons.get(trend, trend.upper())


# ──────────────────────────────────────────────
# Main analysis flow
# ──────────────────────────────────────────────
if run_btn:
    with st.spinner(f"Fetching live data for {pair}…"):
        try:
            tf_data = fetch_multi_timeframe(pair)
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            st.stop()

    with st.spinner("Running market structure analysis…"):
        analysis = get_multi_timeframe_bias(tf_data)

    # ── Summary row ──
    st.subheader(f"Analysis for {pair}  ·  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        trend_4h = analysis["trend_4h"]
        st.metric("4H Trend", trend_badge(trend_4h))
    with col2:
        trend_1h = analysis["trend_1h"]
        st.metric("1H Trend", trend_badge(trend_1h))
    with col3:
        trend_5m = analysis["trend_5m"]
        st.metric("5M Trend", trend_badge(trend_5m))
    with col4:
        bias = analysis["overall_bias"]
        st.metric("Overall Bias", f"{bias_color(bias)}  {bias.upper()}")

    st.markdown("---")

    # ── Trade Idea ──
    trade = analysis["trade_idea"]
    direction = trade["direction"]

    direction_color = {
        "BUY": "success",
        "SELL": "error",
        "NEUTRAL": "warning",
    }
    direction_icon = {"BUY": "📗", "SELL": "📕", "NEUTRAL": "📒"}

    icon = direction_icon.get(direction, "📒")
    st.subheader(f"{icon} Trade Idea: **{direction}**")

    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"**Reason:** {trade['reason']}")
        st.info(f"**Entry note:** {trade['entry_note']}")
    with col_b:
        st.info(f"**Risk/Reward:** {trade['rr_note']}")

        # Key levels
        tf_results = analysis["timeframe_results"]
        sp_1h = tf_results.get("1h", {}).get("structure_points", [])
        levels = get_key_levels(sp_1h, n=3)

        st.markdown("**Key 1H levels**")
        high_prices = [f"{p['price']:.5f} ({p['type']})" for p in levels["recent_highs"]]
        low_prices = [f"{p['price']:.5f} ({p['type']})" for p in levels["recent_lows"]]
        if high_prices:
            st.markdown("Resistance: " + "  ·  ".join(reversed(high_prices)))
        if low_prices:
            st.markdown("Support:    " + "  ·  ".join(reversed(low_prices)))

    st.markdown("---")

    # ── Chart ──
    tf_result = tf_results.get(chart_tf, {})
    df_chart = tf_data.get(chart_tf, pd.DataFrame())
    struct_pts = tf_result.get("structure_points", [])
    bos_evts = tf_result.get("bos_events", [])

    st.subheader(f"Chart — {pair} ({chart_tf.upper()})")

    if df_chart.empty:
        st.warning("No data available for the selected timeframe.")
    else:
        fig = build_candlestick_chart(
            df=df_chart,
            structure_points=struct_pts,
            bos_events=bos_evts,
            title=f"{pair} — {chart_tf.upper()} | Trend: {tf_result.get('trend', '?').upper()}",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Structure table ──
    st.subheader(f"Recent Structure Points ({chart_tf.upper()})")
    if struct_pts:
        recent_pts = struct_pts[-10:]  # Last 10 points
        table_data = [
            {
                "Time": p["datetime"].strftime("%Y-%m-%d %H:%M"),
                "Type": p["type"],
                "Price": f"{p['price']:.5f}",
                "Kind": "Swing High" if p["is_high"] else "Swing Low",
            }
            for p in reversed(recent_pts)
        ]
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
    else:
        st.info("Not enough data to detect structure points on this timeframe.")

    # ── BOS events ──
    if bos_evts:
        st.subheader(f"Break of Structure Events ({chart_tf.upper()})")
        bos_data = [
            {
                "Time": b["datetime"].strftime("%Y-%m-%d %H:%M"),
                "Event": "BOS UP ↑" if b["type"] == "BOS_UP" else "BOS DOWN ↓",
                "Price": f"{b['price']:.5f}",
            }
            for b in reversed(bos_evts[-5:])
        ]
        st.dataframe(pd.DataFrame(bos_data), use_container_width=True, hide_index=True)

else:
    # Landing state — show instructions
    st.markdown(
        """
        ### How to use this app

        1. **Select a currency pair** from the sidebar (e.g. EUR/USD, USD/JPY)
        2. **Click "Fetch & Analyze"** to pull live candle data
        3. The app will show you:
           - Trend on each timeframe (4H, 1H, 5M)
           - A trade bias: **BUY**, **SELL**, or **NEUTRAL**
           - Entry notes and risk/reward guidance
           - An interactive chart with structure labels

        ---

        ### What is Market Structure?

        | Label | Meaning |
        |-------|---------|
        | **HH** | Higher High — bullish sign |
        | **HL** | Higher Low — bullish pullback, potential buy zone |
        | **LH** | Lower High — bearish sign, potential sell zone |
        | **LL** | Lower Low — bearish continuation |
        | **BOS ↑** | Break of Structure upward — bullish momentum shift |
        | **BOS ↓** | Break of Structure downward — bearish momentum shift |

        ---

        > ⚠️ **Disclaimer:** This tool is for educational purposes only.
        > It does not constitute financial advice. Always manage your risk carefully.
        """
    )
