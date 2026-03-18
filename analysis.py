"""
forex/analysis.py
-----------------
Multi-timeframe analysis and trade idea generation.

Strategy:
  - 4H and 1H set the bias (bullish / bearish / neutral)
  - 5M is used for entry-level context
  - Bias is Buy, Sell, or Neutral

Trade idea logic:
  - Buy:  higher-timeframe bullish + 5M shows HL (pullback into support)
  - Sell: higher-timeframe bearish + 5M shows LH (pullback into resistance)
  - No signal during consolidation
"""

import pandas as pd
from forex.structure import (
    find_swing_points,
    classify_structure,
    detect_bos,
    determine_trend,
)


def analyze_timeframe(df: pd.DataFrame, swing_window: int = 3) -> dict:
    """
    Run full structure analysis on a single timeframe DataFrame.

    Args:
        df:           OHLC DataFrame
        swing_window: Window size for swing point detection

    Returns:
        dict with:
            - 'df_with_swings': DataFrame with swing_high/swing_low columns
            - 'structure_points': list of structure dicts
            - 'bos_events':      list of BOS events
            - 'trend':           "bullish", "bearish", or "consolidation"
    """
    df_swings = find_swing_points(df, window=swing_window)
    structure_points = classify_structure(df_swings)
    bos_events = detect_bos(structure_points)
    trend = determine_trend(structure_points)

    return {
        "df_with_swings": df_swings,
        "structure_points": structure_points,
        "bos_events": bos_events,
        "trend": trend,
    }


def get_multi_timeframe_bias(tf_data: dict) -> dict:
    """
    Analyze all timeframes and produce a combined trade bias.

    Args:
        tf_data: dict of DataFrames keyed by timeframe string
                 e.g. {"5min": df_5m, "1h": df_1h, "4h": df_4h}

    Returns:
        dict with per-timeframe analysis results + overall bias + trade idea
    """
    results = {}

    # Analyze each timeframe
    swing_windows = {"5min": 3, "1h": 4, "4h": 4}
    for tf, df in tf_data.items():
        window = swing_windows.get(tf, 3)
        results[tf] = analyze_timeframe(df, swing_window=window)

    # --- Determine overall bias ---
    trend_4h = results.get("4h", {}).get("trend", "consolidation")
    trend_1h = results.get("1h", {}).get("trend", "consolidation")
    trend_5m = results.get("5min", {}).get("trend", "consolidation")

    # Higher timeframes (4H, 1H) set the bias
    higher_tf_trends = [trend_4h, trend_1h]
    bullish_count = higher_tf_trends.count("bullish")
    bearish_count = higher_tf_trends.count("bearish")

    if bullish_count >= 2:
        htf_bias = "bullish"
    elif bearish_count >= 2:
        htf_bias = "bearish"
    elif bullish_count > bearish_count:
        htf_bias = "bullish"
    elif bearish_count > bullish_count:
        htf_bias = "bearish"
    else:
        htf_bias = "neutral"

    # --- Generate trade idea ---
    trade_idea = _generate_trade_idea(
        htf_bias=htf_bias,
        trend_5m=trend_5m,
        results=results,
    )

    return {
        "timeframe_results": results,
        "trend_4h": trend_4h,
        "trend_1h": trend_1h,
        "trend_5m": trend_5m,
        "overall_bias": htf_bias,
        "trade_idea": trade_idea,
    }


def _generate_trade_idea(htf_bias: str, trend_5m: str, results: dict) -> dict:
    """
    Generate a trade idea based on multi-timeframe bias.

    Rules:
        BUY signal:   HTF bias is bullish + 5M shows HL (higher low = pullback)
        SELL signal:  HTF bias is bearish + 5M shows LH (lower high = pullback)
        NEUTRAL:      any consolidation or mixed signals

    Returns:
        dict with:
            - 'direction':   "BUY", "SELL", or "NEUTRAL"
            - 'reason':      explanation string
            - 'entry_note':  brief entry guidance
            - 'rr_note':     risk:reward note
    """
    if htf_bias == "neutral":
        return {
            "direction": "NEUTRAL",
            "reason": "Higher timeframes are mixed or in consolidation. No clear bias.",
            "entry_note": "Wait for a clear break of structure on the 4H or 1H.",
            "rr_note": "N/A",
        }

    # Get recent 5M structure points
    structure_5m = results.get("5min", {}).get("structure_points", [])
    recent_5m = [p for p in structure_5m if p["type"] in ("HH", "HL", "LH", "LL")]
    last_5m_types = [p["type"] for p in recent_5m[-4:]]

    if htf_bias == "bullish":
        # Ideal: 5M is in a pullback (showing HL) while HTF is bullish
        if "HL" in last_5m_types and trend_5m != "bearish":
            return {
                "direction": "BUY",
                "reason": (
                    "4H/1H structure is bullish (HH+HL sequence). "
                    "5M shows a Higher Low — price has pulled back into a potential support."
                ),
                "entry_note": (
                    "Look to buy near the 5M HL level. "
                    "Entry on confirmation candle (bullish engulfing or strong close)."
                ),
                "rr_note": "Target: 1:2 risk-reward. Stop below the 5M HL.",
            }
        elif trend_5m == "bullish":
            return {
                "direction": "BUY",
                "reason": (
                    "4H/1H structure is bullish. "
                    "5M is also bullish — continuation trade possible."
                ),
                "entry_note": (
                    "Wait for a minor pullback on 5M (HL formation) "
                    "before entering long."
                ),
                "rr_note": "Target: 1:2 risk-reward. Stop below last 5M swing low.",
            }
        else:
            return {
                "direction": "NEUTRAL",
                "reason": (
                    "4H/1H are bullish but 5M is in consolidation or bearish. "
                    "Wait for 5M to confirm."
                ),
                "entry_note": "Watch for 5M HL formation before buying.",
                "rr_note": "N/A",
            }

    else:  # bearish
        if "LH" in last_5m_types and trend_5m != "bullish":
            return {
                "direction": "SELL",
                "reason": (
                    "4H/1H structure is bearish (LH+LL sequence). "
                    "5M shows a Lower High — price has pulled back into a potential resistance."
                ),
                "entry_note": (
                    "Look to sell near the 5M LH level. "
                    "Entry on confirmation candle (bearish engulfing or strong close down)."
                ),
                "rr_note": "Target: 1:2 risk-reward. Stop above the 5M LH.",
            }
        elif trend_5m == "bearish":
            return {
                "direction": "SELL",
                "reason": (
                    "4H/1H structure is bearish. "
                    "5M is also bearish — continuation trade possible."
                ),
                "entry_note": (
                    "Wait for a minor pullback on 5M (LH formation) "
                    "before entering short."
                ),
                "rr_note": "Target: 1:2 risk-reward. Stop above last 5M swing high.",
            }
        else:
            return {
                "direction": "NEUTRAL",
                "reason": (
                    "4H/1H are bearish but 5M is in consolidation or bullish. "
                    "Wait for 5M to confirm."
                ),
                "entry_note": "Watch for 5M LH formation before selling.",
                "rr_note": "N/A",
            }


def get_key_levels(structure_points: list, n: int = 4) -> dict:
    """
    Extract the most recent key price levels from structure points.

    Args:
        structure_points: list of structure dicts
        n:                how many recent points to return

    Returns:
        dict with 'recent_highs' and 'recent_lows' lists
    """
    highs = [p for p in structure_points if p["is_high"]]
    lows = [p for p in structure_points if not p["is_high"]]

    return {
        "recent_highs": highs[-n:],
        "recent_lows": lows[-n:],
    }
