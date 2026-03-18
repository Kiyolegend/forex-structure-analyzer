"""
forex/structure.py
------------------
Market structure detection:
  - Swing highs and lows (using a simple pivot-based method)
  - Structure classification: HH, HL, LH, LL
  - Break of structure (BOS) detection
  - Trend classification: bullish, bearish, consolidation
"""

import pandas as pd
import numpy as np


def find_swing_points(df: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    """
    Identify swing highs and swing lows in price data.

    A swing HIGH is a candle whose high is the highest in the
    surrounding `window` candles on each side.

    A swing LOW is a candle whose low is the lowest in the
    surrounding `window` candles on each side.

    Args:
        df:     OHLC DataFrame (must have 'high', 'low', 'datetime' columns).
        window: Number of candles to look on each side (default 3).

    Returns:
        DataFrame with added columns:
            - 'swing_high': True if this bar is a swing high
            - 'swing_low':  True if this bar is a swing low
    """
    df = df.copy()
    df["swing_high"] = False
    df["swing_low"] = False

    for i in range(window, len(df) - window):
        # Check for swing high
        local_high = df["high"].iloc[i]
        left_highs = df["high"].iloc[i - window : i]
        right_highs = df["high"].iloc[i + 1 : i + window + 1]
        if local_high > left_highs.max() and local_high > right_highs.max():
            df.at[df.index[i], "swing_high"] = True

        # Check for swing low
        local_low = df["low"].iloc[i]
        left_lows = df["low"].iloc[i - window : i]
        right_lows = df["low"].iloc[i + 1 : i + window + 1]
        if local_low < left_lows.min() and local_low < right_lows.min():
            df.at[df.index[i], "swing_low"] = True

    return df


def classify_structure(df: pd.DataFrame) -> list:
    """
    Classify market structure as HH, HL, LH, or LL by comparing
    consecutive swing highs and swing lows.

    Args:
        df: DataFrame with 'swing_high', 'swing_low', 'high', 'low', 'datetime' columns.

    Returns:
        List of dicts, each with:
            - 'type':     "HH", "HL", "LH", or "LL"
            - 'price':    price level of the swing point
            - 'datetime': timestamp
            - 'is_high':  True if it was a swing high, False if swing low
    """
    # Collect all swing points in chronological order
    swing_highs = df[df["swing_high"]].copy()
    swing_highs["point_type"] = "high"
    swing_highs["price"] = swing_highs["high"]

    swing_lows = df[df["swing_low"]].copy()
    swing_lows["point_type"] = "low"
    swing_lows["price"] = swing_lows["low"]

    # Merge and sort by datetime
    swings = pd.concat(
        [
            swing_highs[["datetime", "price", "point_type"]],
            swing_lows[["datetime", "price", "point_type"]],
        ]
    ).sort_values("datetime").reset_index(drop=True)

    if len(swings) < 2:
        return []

    structure_points = []

    # Track last high and last low separately
    last_high = None
    last_low = None

    for _, row in swings.iterrows():
        if row["point_type"] == "high":
            if last_high is not None:
                label = "HH" if row["price"] > last_high["price"] else "LH"
                structure_points.append({
                    "type": label,
                    "price": row["price"],
                    "datetime": row["datetime"],
                    "is_high": True,
                })
            else:
                structure_points.append({
                    "type": "SH",  # First swing high, no comparison yet
                    "price": row["price"],
                    "datetime": row["datetime"],
                    "is_high": True,
                })
            last_high = row

        else:  # swing low
            if last_low is not None:
                label = "HL" if row["price"] > last_low["price"] else "LL"
                structure_points.append({
                    "type": label,
                    "price": row["price"],
                    "datetime": row["datetime"],
                    "is_high": False,
                })
            else:
                structure_points.append({
                    "type": "SL",  # First swing low, no comparison yet
                    "price": row["price"],
                    "datetime": row["datetime"],
                    "is_high": False,
                })
            last_low = row

    return structure_points


def detect_bos(structure_points: list) -> list:
    """
    Detect Break of Structure (BOS) events.

    A bullish BOS occurs when price breaks above the most recent swing high (LH broken → BOS Up).
    A bearish BOS occurs when price breaks below the most recent swing low (HL broken → BOS Down).

    This is simplified: we look for a transition from LH to HH (bullish BOS)
    or from HL to LL (bearish BOS).

    Args:
        structure_points: List of structure dicts from classify_structure().

    Returns:
        List of BOS event dicts with 'type' ("BOS_UP" or "BOS_DOWN"),
        'price', and 'datetime'.
    """
    bos_events = []
    prev = None

    for point in structure_points:
        if prev is not None:
            # Bullish BOS: previous was LH (lower high), current is HH (higher high)
            if prev["type"] == "LH" and point["type"] == "HH":
                bos_events.append({
                    "type": "BOS_UP",
                    "price": point["price"],
                    "datetime": point["datetime"],
                })
            # Bearish BOS: previous was HL (higher low), current is LL (lower low)
            elif prev["type"] == "HL" and point["type"] == "LL":
                bos_events.append({
                    "type": "BOS_DOWN",
                    "price": point["price"],
                    "datetime": point["datetime"],
                })
        prev = point

    return bos_events


def determine_trend(structure_points: list) -> str:
    """
    Determine overall trend from the last few structure points.

    Rules:
        - Bullish:       sequence contains HH and HL (higher highs + higher lows)
        - Bearish:       sequence contains LH and LL (lower highs + lower lows)
        - Consolidation: mixed or insufficient data

    Args:
        structure_points: List of structure dicts from classify_structure().

    Returns:
        "bullish", "bearish", or "consolidation"
    """
    if len(structure_points) < 4:
        return "consolidation"

    # Look at the last 6 structure points for trend assessment
    recent = structure_points[-6:]
    types = [p["type"] for p in recent]

    hh_count = types.count("HH")
    hl_count = types.count("HL")
    lh_count = types.count("LH")
    ll_count = types.count("LL")

    bullish_score = hh_count + hl_count
    bearish_score = lh_count + ll_count

    if bullish_score >= 3 and bullish_score > bearish_score:
        return "bullish"
    elif bearish_score >= 3 and bearish_score > bullish_score:
        return "bearish"
    else:
        return "consolidation"
