"""Hybrid BUY / SELL / HOLD scoring engine.

Design principles (from spec section 8):
  * No single indicator decides the outcome. The final score is a weighted blend
    of independently-computed sub-scores, each normalized to [-100, +100].
  * The LLM does NOT produce the numeric score. It only explains a score this
    engine has already computed. This module is pure Python and deterministic.
  * Confidence is a CALIBRATION estimate, never a promise of profit. It is derived
    from (a) agreement between sub-scores and (b) optional historical hit-rate for
    the active weight-set at similar score bands.

Every numeric input is expected pre-normalized to [-100, 100] by the feature layer
(technical/fundamental/news/... services). This keeps the engine testable in isolation.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Optional

from .weights import ScoringWeights, DEFAULT_WEIGHTS

MODEL_VERSION = "engine-1.0"


@dataclass
class SubScores:
    """All values in [-100, 100]. Missing inputs default to 0 (neutral)."""
    technical: float = 0.0
    fundamental: float = 0.0
    news: float = 0.0
    market_sentiment: float = 0.0
    institutional: float = 0.0        # FII/DII + bulk/block deal impact
    options: float = 0.0
    global_market: float = 0.0
    other: float = 0.0                # volatility, risk overlays, misc

    def as_dict(self) -> dict:
        return {
            "technical": self.technical,
            "fundamental": self.fundamental,
            "news": self.news,
            "market_sentiment": self.market_sentiment,
            "institutional": self.institutional,
            "options": self.options,
            "global_market": self.global_market,
            "other": self.other,
        }


@dataclass
class TradeLevels:
    entry_price: Optional[float] = None
    target1: Optional[float] = None
    target2: Optional[float] = None
    stop_loss: Optional[float] = None
    risk_reward: Optional[float] = None


@dataclass
class Signal:
    label: str
    final_score: float
    confidence: float
    subscores: dict
    reasons: list[str]
    levels: TradeLevels
    weights_version: str
    model_version: str = MODEL_VERSION

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "final_score": round(self.final_score, 2),
            "confidence": round(self.confidence, 2),
            "subscores": {k: round(v, 2) for k, v in self.subscores.items()},
            "reasons": self.reasons,
            "entry_price": self.levels.entry_price,
            "target1": self.levels.target1,
            "target2": self.levels.target2,
            "stop_loss": self.levels.stop_loss,
            "risk_reward": self.levels.risk_reward,
            "weights_version": self.weights_version,
            "model_version": self.model_version,
        }


def _clamp(x: float, lo: float = -100.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def label_for_score(score: float) -> str:
    """Map final score [-100,100] to a 6-way label."""
    if score >= 60:
        return "STRONG_BUY"
    if score >= 25:
        return "BUY"
    if score > -25:
        return "HOLD"
    if score > -60:
        return "AVOID"          # mild negative: don't hold, but not an active short
    return "STRONG_SELL"        # deep negative
    # NOTE: plain "SELL" is emitted below when score in (-60,-40] for existing holders.


def _refine_label(score: float) -> str:
    if score >= 60:
        return "STRONG_BUY"
    if score >= 25:
        return "BUY"
    if score > -25:
        return "HOLD"
    if score > -45:
        return "AVOID"
    if score > -60:
        return "SELL"
    return "STRONG_SELL"


def compute_confidence(
    subscores: SubScores,
    final_score: float,
    historical_hit_rate: Optional[float] = None,
    active_factors: Optional[set[str]] = None,
) -> float:
    """Confidence in [0,100].

    Two ingredients:
      1. Agreement: if sub-scores mostly point the same direction, we're more
         confident. Measured as 100 minus the spread (stdev) of the sub-scores,
         scaled. High disagreement -> low confidence even with a strong mean.
      2. Magnitude: stronger absolute final score -> more confidence.
    If a calibrated historical hit-rate for this score band is supplied, we blend
    it in so "70% confidence" is tied to real out-of-sample performance (spec 12).
    """
    d = subscores.as_dict()
    active = active_factors or set(d.keys())
    vals = [d[f] for f in d if f in active] or [0.0]
    spread = statistics.pstdev(vals) if len(vals) > 1 else 0.0
    agreement = _clamp(100.0 - spread, 0.0, 100.0)          # 0..100
    magnitude = min(abs(final_score) / 100.0 * 100.0, 100.0)  # 0..100

    # Coverage: fewer live factors -> less confidence (max ~1.0 at 4+ factors)
    coverage = min(len(vals) / 4.0, 1.0)

    base = (0.6 * agreement + 0.4 * magnitude) * (0.6 + 0.4 * coverage)

    if historical_hit_rate is not None:
        # historical_hit_rate is 0..1 empirical accuracy for this weight-set/band.
        base = 0.5 * base + 0.5 * (historical_hit_rate * 100.0)

    return round(_clamp(base, 0.0, 100.0), 2)


def compute_levels(
    entry: Optional[float],
    label: str,
    atr: Optional[float] = None,
    support: Optional[float] = None,
    resistance: Optional[float] = None,
) -> TradeLevels:
    """Derive entry/target/SL. Prefers structure (support/resistance); falls back
    to an ATR multiple. Returns empty levels for HOLD or when no price is known.
    These are analytical levels, NOT advice and NOT a guarantee.
    """
    if entry is None or label in ("HOLD",):
        return TradeLevels()

    bullish = label in ("STRONG_BUY", "BUY")
    unit = atr if atr else entry * 0.02   # default 2% risk unit if no ATR

    if bullish:
        stop = support if (support and support < entry) else entry - 1.5 * unit
        t1 = resistance if (resistance and resistance > entry) else entry + 1.5 * unit
        t2 = entry + 3.0 * unit
        risk = entry - stop
        reward = t1 - entry
    else:  # bearish (AVOID/SELL/STRONG_SELL) — levels framed for a short view
        stop = resistance if (resistance and resistance > entry) else entry + 1.5 * unit
        t1 = support if (support and support < entry) else entry - 1.5 * unit
        t2 = entry - 3.0 * unit
        risk = stop - entry
        reward = entry - t1

    rr = round(abs(reward / risk), 2) if risk not in (0, None) else None
    return TradeLevels(
        entry_price=round(entry, 2),
        target1=round(t1, 2),
        target2=round(t2, 2),
        stop_loss=round(stop, 2),
        risk_reward=rr,
    )


# Human-readable reason templates keyed by sub-score sign/strength.
_REASON_RULES = [
    ("technical",        30,  "Bullish technical structure (trend/RSI/MACD aligned)"),
    ("technical",       -30,  "Bearish technical structure"),
    ("fundamental",      30,  "Strong fundamentals (growth/margins/returns)"),
    ("fundamental",     -30,  "Weak fundamentals / stretched valuation"),
    ("news",             30,  "Positive news sentiment"),
    ("news",            -30,  "Negative news sentiment"),
    ("market_sentiment", 30,  "Supportive broad-market sentiment"),
    ("market_sentiment",-30,  "Weak broad-market sentiment"),
    ("institutional",    30,  "Institutional buying / positive FII-DII flow"),
    ("institutional",   -30,  "Institutional selling / negative flow"),
    ("options",          30,  "Options positioning bullish (OI/PCR)"),
    ("options",         -30,  "Options positioning bearish"),
    ("global_market",    30,  "Favourable global cues"),
    ("global_market",   -30,  "Adverse global cues"),
]


def build_reasons(subscores: SubScores) -> list[str]:
    d = subscores.as_dict()
    reasons: list[str] = []
    for key, threshold, text in _REASON_RULES:
        v = d.get(key, 0.0)
        if threshold > 0 and v >= threshold:
            reasons.append(text)
        elif threshold < 0 and v <= threshold:
            reasons.append(text)
    return reasons or ["No strong directional factors; signal is near-neutral"]


_FACTORS = ("technical", "fundamental", "news", "market_sentiment",
            "institutional", "options", "global_market", "other")


def _effective_weights(weights: ScoringWeights, active: Optional[set[str]]) -> dict:
    """Return per-factor weights renormalized over the ACTIVE factors.

    A factor with no data must not count as a neutral (0) vote — that would bias
    every signal toward HOLD until all feeds are wired. Instead we drop inactive
    factors and rescale the remaining weights to sum to 1, so the signal reflects
    only what is actually known.
    """
    wd = weights.as_dict()
    wd.pop("version", None)
    if not active:
        active = set(_FACTORS)
    total = sum(wd[f] for f in _FACTORS if f in active)
    if total <= 0:
        return {f: 0.0 for f in _FACTORS}
    return {f: (wd[f] / total if f in active else 0.0) for f in _FACTORS}


def score_stock(
    subscores: SubScores,
    weights: ScoringWeights = DEFAULT_WEIGHTS,
    entry_price: Optional[float] = None,
    atr: Optional[float] = None,
    support: Optional[float] = None,
    resistance: Optional[float] = None,
    historical_hit_rate: Optional[float] = None,
    active_factors: Optional[set[str]] = None,
) -> Signal:
    """Main entry point. Blend sub-scores -> Signal.

    active_factors: names of factors that have real data this run. Missing factors
    are excluded and weights renormalized. Defaults to all factors.
    """
    weights.validate()
    d = subscores.as_dict()
    ew = _effective_weights(weights, active_factors)

    final = _clamp(sum(ew[f] * d[f] for f in _FACTORS))

    label = _refine_label(final)
    confidence = compute_confidence(subscores, final, historical_hit_rate, active_factors)
    levels = compute_levels(entry_price, label, atr, support, resistance)
    reasons = build_reasons(subscores)

    return Signal(
        label=label,
        final_score=final,
        confidence=confidence,
        subscores=d,
        reasons=reasons,
        levels=levels,
        weights_version=weights.version,
    )


if __name__ == "__main__":
    # Quick smoke test — runnable with `python -m app.scoring.engine`
    demo = SubScores(
        technical=70, fundamental=40, news=55, market_sentiment=35,
        institutional=75, options=30, global_market=20, other=10,
    )
    sig = score_stock(demo, entry_price=1250, support=1210, resistance=1300,
                      historical_hit_rate=0.70)
    import json
    print(json.dumps(sig.as_dict(), indent=2))
