"""Stock analysis routes."""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.analysis import analyze_stock

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/{symbol}/analysis")
async def stock_analysis(
    symbol: str,
    exchange: str = Query("NSE", pattern="^(NSE|BSE)$"),
    hit_rate: float | None = Query(None, ge=0, le=1,
                                   description="Optional calibrated historical hit-rate"),
):
    """Full AI analysis for a stock: indicators + signal + freshness + disclaimer."""
    return await analyze_stock(symbol.upper(), exchange, historical_hit_rate=hit_rate)


@router.get("/{symbol}")
async def stock_summary(symbol: str, exchange: str = Query("NSE", pattern="^(NSE|BSE)$")):
    """Lightweight summary: latest price + label only."""
    res = await analyze_stock(symbol.upper(), exchange)
    if "error" in res:
        return res
    return {
        "symbol": res["symbol"],
        "exchange": res["exchange"],
        "price": res["indicators"]["price"],
        "label": res["signal"]["label"],
        "confidence": res["signal"]["confidence"],
        "data_timestamp": res["data_timestamp"],
        "disclaimer": res["disclaimer"],
    }
