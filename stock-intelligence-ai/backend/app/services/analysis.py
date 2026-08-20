"""Analysis orchestrator — the end-to-end pipeline for one stock.

fetch candles (provider + cache)  ->  indicators  ->  sub-scores  ->  scoring engine
Returns a full analysis payload: indicators, sub-scores, the signal, data freshness,
and the mandatory disclaimer. This is what /stock/{symbol}/analysis serves.

News/fundamentals/institutional/options/global inputs are accepted as optional
pre-normalized sub-scores; when a real feed isn't wired for a factor it stays neutral
(0) and the signal is driven by the factors that ARE available (currently technical).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.cache import get_cache
from app.providers.registry import get_history_fn
from app.scoring.engine import SubScores, score_stock
from app.scoring.weights import DEFAULT_WEIGHTS, ScoringWeights
from app.services import features
from app.services.indicators import compute_indicators

DISCLAIMER = (
    "AI-based analysis for research/education only. Not investment advice, not a "
    "guarantee of accuracy or profit. Not SEBI-registered advice. Make your own decisions."
)


async def _get_candles(symbol: str, exchange: str, interval: str = "1d") -> tuple[list, str, str]:
    cache = get_cache()
    key = f"candles:{exchange}:{symbol}:{interval}"
    cached = await cache.get(key)
    if cached:
        return cached["data"], cached["source"], cached["fetched_at"]

    hist = get_history_fn()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=200)
    res = await hist(symbol, exchange, interval, start, end)
    fetched_at = res.fetched_at.isoformat()
    ttl = 60 if interval.endswith("m") else 900   # intraday fresher than daily
    await cache.set(key, {"data": res.data, "source": res.source,
                          "fetched_at": fetched_at}, ttl=ttl)
    return res.data, res.source, fetched_at


async def analyze_stock(
    symbol: str,
    exchange: str = "NSE",
    *,
    weights: ScoringWeights = DEFAULT_WEIGHTS,
    fundamentals: Optional[dict] = None,
    news_items: Optional[list[dict]] = None,
    fii_dii_net: float = 0.0,
    bulk_deal_bias: float = 0.0,
    options_score: Optional[float] = None,
    global_score: Optional[float] = None,
    market_sentiment: Optional[float] = None,
    historical_hit_rate: Optional[float] = None,
) -> dict:
    candles, source, fetched_at = await _get_candles(symbol, exchange)
    ind = compute_indicators(candles)
    if ind is None:
        return {"error": "insufficient_data", "symbol": symbol,
                "disclaimer": DISCLAIMER}

    sub = SubScores(
        technical=features.technical_score(ind),
        fundamental=features.fundamental_score(fundamentals),
        news=features.news_score(news_items),
        market_sentiment=features.passthrough(market_sentiment),
        institutional=features.institutional_score(
            fii_dii_net=fii_dii_net, bulk_deal_bias=bulk_deal_bias),
        options=features.passthrough(options_score),
        global_market=features.passthrough(global_score),
        other=0.0,
    )

    # Only factors with real data this run participate; the rest are excluded
    # (not treated as neutral) so the signal reflects what's actually known.
    active = {"technical"}
    if fundamentals:
        active.add("fundamental")
    if news_items:
        active.add("news")
    if market_sentiment is not None:
        active.add("market_sentiment")
    if fii_dii_net or bulk_deal_bias:
        active.add("institutional")
    if options_score is not None:
        active.add("options")
    if global_score is not None:
        active.add("global_market")

    signal = score_stock(
        sub, weights=weights,
        entry_price=ind["price"], atr=ind["atr"],
        support=ind["support"], resistance=ind["resistance"],
        historical_hit_rate=historical_hit_rate,
        active_factors=active,
    )

    return {
        "symbol": symbol,
        "exchange": exchange,
        "indicators": ind,
        "signal": signal.as_dict(),
        "data_source": source,
        "data_timestamp": fetched_at,
        "disclaimer": DISCLAIMER,
    }
