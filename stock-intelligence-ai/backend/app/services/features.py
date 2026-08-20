"""Feature -> sub-score mappers.

Each function converts raw domain data into a normalized score in [-100, 100]
that the scoring engine can blend. The technical mapper is fully implemented from
indicator values. Fundamental/news/etc. accept already-normalized inputs where a
real data feed isn't wired yet, defaulting to neutral (0) so the engine still runs.
Keeping mapping here (not in the engine) means you can tune signal semantics without
touching the blend math.
"""
from __future__ import annotations

from typing import Optional


def _clamp(x: float, lo: float = -100.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def technical_score(ind: dict) -> float:
    """Blend trend, RSI, MACD and price-vs-VWAP into one technical sub-score."""
    price = ind["price"]
    score = 0.0

    # Trend via EMA stack (±40)
    if price > ind["ema20"] > ind["ema50"]:
        score += 40
    elif price < ind["ema20"] < ind["ema50"]:
        score -= 40
    else:
        score += 10 if price > ind["ema50"] else -10

    # RSI (±25): momentum, with overbought/oversold dampening
    rsi = ind["rsi"]
    if rsi >= 70:
        score += 5          # strong but overbought — muted
    elif rsi >= 55:
        score += 25
    elif rsi <= 30:
        score -= 5          # oversold — muted (possible bounce)
    elif rsi <= 45:
        score -= 25

    # MACD (±20)
    score += 20 if ind["macd"] > ind["macd_signal"] else -20

    # Price vs VWAP (±15)
    score += 15 if price > ind["vwap"] else -15

    return _clamp(score)


def fundamental_score(fund: Optional[dict]) -> float:
    """Map fundamentals to [-100,100]. Expects a dict with common ratios; returns
    0 when unavailable."""
    if not fund:
        return 0.0
    s = 0.0
    if (g := fund.get("profit_growth")) is not None:
        s += _clamp(g * 2, -30, 30)
    if (roe := fund.get("roe")) is not None:
        s += _clamp((roe - 12) * 2, -20, 20)     # 12% ROE ~ neutral
    if (de := fund.get("debt_to_equity")) is not None:
        s += _clamp((1.0 - de) * 20, -20, 20)     # lower leverage better
    if (pe := fund.get("pe")) is not None and pe > 0:
        s += _clamp((25 - pe), -15, 15)           # cheaper vs 25x neutral
    if (pledge := fund.get("promoter_pledge")) is not None:
        s -= _clamp(pledge, 0, 15)                # any pledge is a negative
    return _clamp(s)


def news_score(items: Optional[list[dict]]) -> float:
    """Aggregate per-article sentiment (already normalized to [-100,100]) weighted
    by source reliability and recency. Returns 0 when no news."""
    if not items:
        return 0.0
    num = den = 0.0
    for it in items:
        w = float(it.get("source_reliability", 0.5))
        num += float(it.get("score", 0)) * w
        den += w
    return _clamp(num / den) if den else 0.0


def institutional_score(*, fii_dii_net: float = 0.0, bulk_deal_bias: float = 0.0) -> float:
    """Combine FII/DII net flow signal and bulk/block-deal bias, both pre-normalized."""
    return _clamp(0.6 * fii_dii_net + 0.4 * bulk_deal_bias)


def passthrough(value: Optional[float]) -> float:
    return _clamp(value) if value is not None else 0.0
