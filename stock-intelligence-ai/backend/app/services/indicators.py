"""Technical indicators computed from OHLCV candles (pure pandas — no TA-Lib).

Input: list of candles [ts, open, high, low, close, volume] (Angel One's shape).
Output: a dict of indicator values + a trend label + swing support/resistance.
Kept dependency-light so it installs cleanly in any environment.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def _to_df(candles: list[list]) -> pd.DataFrame:
    df = pd.DataFrame(candles, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"])
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna().reset_index(drop=True)


def _ema(s: pd.Series, span: int) -> float:
    return float(s.ewm(span=span, adjust=False).mean().iloc[-1])


def _rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    val = rsi.iloc[-1]
    return float(val) if pd.notna(val) else 50.0


def _macd(close: pd.Series) -> tuple[float, float]:
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return float(macd.iloc[-1]), float(signal.iloc[-1])


def _bollinger(close: pd.Series, period: int = 20, k: float = 2.0) -> tuple[float, float]:
    ma = close.rolling(period).mean()
    sd = close.rolling(period).std()
    upper = ma + k * sd
    lower = ma - k * sd
    return float(upper.iloc[-1]), float(lower.iloc[-1])


def _vwap(df: pd.DataFrame) -> float:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    cum_vol = df["volume"].cumsum().replace(0, np.nan)
    vwap = (tp * df["volume"]).cumsum() / cum_vol
    val = vwap.iloc[-1]
    return float(val) if pd.notna(val) else float(df["close"].iloc[-1])


def _support_resistance(df: pd.DataFrame, window: int = 20) -> tuple[float, float]:
    recent = df.tail(window)
    return float(recent["low"].min()), float(recent["high"].max())


def compute_indicators(candles: list[list]) -> Optional[dict]:
    """Return indicator dict or None if insufficient data."""
    if not candles or len(candles) < 30:
        return None
    df = _to_df(candles)
    if len(df) < 30:
        return None

    close = df["close"]
    price = float(close.iloc[-1])
    ema20, ema50, ema200 = _ema(close, 20), _ema(close, 50), _ema(close, min(200, len(df)))
    rsi = _rsi(close)
    macd, macd_sig = _macd(close)
    bb_u, bb_l = _bollinger(close)
    vwap = _vwap(df)
    support, resistance = _support_resistance(df)

    if price > ema20 > ema50:
        trend = "UP"
    elif price < ema20 < ema50:
        trend = "DOWN"
    else:
        trend = "SIDEWAYS"

    # crude ATR proxy for level-setting
    tr = (df["high"] - df["low"]).tail(14).mean()

    return {
        "price": round(price, 2),
        "ema20": round(ema20, 2), "ema50": round(ema50, 2), "ema200": round(ema200, 2),
        "rsi": round(rsi, 2),
        "macd": round(macd, 4), "macd_signal": round(macd_sig, 4),
        "bb_upper": round(bb_u, 2), "bb_lower": round(bb_l, 2),
        "vwap": round(vwap, 2),
        "support": round(support, 2), "resistance": round(resistance, 2),
        "atr": round(float(tr), 2),
        "trend": trend,
    }
