"""Configurable scoring weights.

Weights are versioned so every stored signal records which weight-set produced it
(see ai_signals.weights_version). This lets you A/B weight-sets and compare
their historical performance in signal_performance.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass(frozen=True)
class ScoringWeights:
    version: str = "w1.0"
    technical: float = 0.20
    fundamental: float = 0.15
    news: float = 0.15
    market_sentiment: float = 0.15
    institutional: float = 0.10
    options: float = 0.10
    global_market: float = 0.10
    other: float = 0.05

    def as_dict(self) -> dict:
        return asdict(self)

    def validate(self) -> None:
        total = (
            self.technical + self.fundamental + self.news + self.market_sentiment
            + self.institutional + self.options + self.global_market + self.other
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {total:.4f}")


# Default active weight-set. Override per-request or per-user risk profile.
DEFAULT_WEIGHTS = ScoringWeights()
