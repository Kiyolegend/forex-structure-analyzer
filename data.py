"""
forex/data.py
-------------
Fetches live OHLC candle data from the Twelve Data API.
Supports multiple timeframes: 1min, 5min, 1h, 4h
"""

import os
import requests
import pandas as pd


TWELVE_DATA_BASE_URL = "https://api.twelvedata.com"

# Supported forex pairs
SUPPORTED_PAIRS = [
    "USD/JPY",
    "EUR/USD",
    "GBP/USD",
    "AUD/USD",
    "USD/CAD",
    "USD/CHF",
    "EUR/JPY",
    "GBP/JPY",
]

# Timeframe labels
TIMEFRAMES = {
    "1min": "1min",
    "5min": "5min",
    "1h": "1h",
    "4h": "4h",
}


def get_api_key() -> str:
    """Read API key from environment variable."""
    key = os.environ.get("TWELVE_DATA_API_KEY", "")
    if not key:
        raise ValueError("TWELVE_DATA_API_KEY environment variable is not set.")
    return key


def fetch_candles(symbol: str, interval: str, outputsize: int = 100) -> pd.DataFrame:
    """
    Fetch OHLC candle data from Twelve Data.

    Args:
        symbol:     Forex pair, e.g. "EUR/USD"
        interval:   Timeframe string, e.g. "1min", "5min", "1h", "4h"
        outputsize: Number of candles to fetch (max 5000 on paid plans, 800 on free)

    Returns:
        DataFrame with columns: datetime, open, high, low, close
        Sorted oldest → newest (ascending by time).
    """
    api_key = get_api_key()

    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": api_key,
        "format": "JSON",
    }

    response = requests.get(
        f"{TWELVE_DATA_BASE_URL}/time_series",
        params=params,
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    # Check for API-level errors
    if data.get("status") == "error" or "values" not in data:
        msg = data.get("message", "Unknown error from Twelve Data API")
        raise RuntimeError(f"Twelve Data API error: {msg}")

    # Parse into DataFrame
    df = pd.DataFrame(data["values"])
    df = df.rename(columns={"datetime": "datetime"})

    # Convert types
    df["datetime"] = pd.to_datetime(df["datetime"])
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col])

    # Sort ascending (oldest first)
    df = df.sort_values("datetime").reset_index(drop=True)

    return df


def fetch_multi_timeframe(symbol: str) -> dict:
    """
    Fetch candles for all relevant timeframes for a given pair.

    Returns:
        dict with keys "5min", "1h", "4h" each containing a DataFrame.
        Note: We skip 1min to preserve API quota on the free tier.
    """
    timeframes_to_fetch = {
        "5min": 100,
        "1h": 100,
        "4h": 60,
    }

    result = {}
    for tf, size in timeframes_to_fetch.items():
        df = fetch_candles(symbol, interval=tf, outputsize=size)
        result[tf] = df

    return result
