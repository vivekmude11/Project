"""FastAPI entrypoint.

M1 ships a health check and a demo /score endpoint that exercises the scoring
engine end-to-end so you can run the backend today. Real data-backed routes
(/stock/{symbol}/analysis, /signals, /market/*) land in M2–M3 once the provider
adapters are wired.
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.scoring.engine import SubScores, score_stock
from app.scoring.weights import DEFAULT_WEIGHTS, ScoringWeights
from app.api import routes_stock, routes_auth, routes_portfolio

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "AI-based stock market ANALYSIS & RESEARCH tool for Indian markets. "
        "Not investment advice. Not SEBI-registered advice unless all applicable "
        "regulatory requirements are met. No guaranteed returns."
    ),
)

app.include_router(routes_stock.router)
app.include_router(routes_auth.router)
app.include_router(routes_portfolio.router)

DISCLAIMER = (
    "AI-based analysis for research/education only. Not investment advice, not a "
    "guarantee of accuracy or profit. Not SEBI-registered advice. Make your own decisions."
)


@app.on_event("startup")
async def _ensure_tables() -> None:
    """Create ORM tables if missing. schema.sql already provisions the full schema
    when Postgres first boots via docker-compose; this is a safety net for the ORM
    subset and is a no-op if they exist. Failures are non-fatal in dev (no DB)."""
    try:
        from app.models.db import Base, engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:  # noqa: BLE001 — dev may run without a DB
        import logging
        logging.getLogger(__name__).warning("Skipping table init (no DB?): %s", e)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "env": settings.environment}


class ScoreRequest(BaseModel):
    technical: float = Field(0, ge=-100, le=100)
    fundamental: float = Field(0, ge=-100, le=100)
    news: float = Field(0, ge=-100, le=100)
    market_sentiment: float = Field(0, ge=-100, le=100)
    institutional: float = Field(0, ge=-100, le=100)
    options: float = Field(0, ge=-100, le=100)
    global_market: float = Field(0, ge=-100, le=100)
    other: float = Field(0, ge=-100, le=100)
    entry_price: float | None = None
    support: float | None = None
    resistance: float | None = None
    atr: float | None = None
    historical_hit_rate: float | None = Field(None, ge=0, le=1)


@app.post("/score")
async def score(req: ScoreRequest) -> dict:
    """Demo endpoint: feed normalized sub-scores, get a signal back.
    In production the sub-scores are computed by the feature services, not the client."""
    sub = SubScores(
        technical=req.technical, fundamental=req.fundamental, news=req.news,
        market_sentiment=req.market_sentiment, institutional=req.institutional,
        options=req.options, global_market=req.global_market, other=req.other,
    )
    sig = score_stock(
        sub, weights=DEFAULT_WEIGHTS, entry_price=req.entry_price,
        atr=req.atr, support=req.support, resistance=req.resistance,
        historical_hit_rate=req.historical_hit_rate,
    )
    return {"signal": sig.as_dict(), "disclaimer": DISCLAIMER}
