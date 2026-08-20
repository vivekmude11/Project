"""Portfolio routes: positions with live P/L and a hold/sell hint derived from the
current AI signal. Does not execute trades (spec section 11)."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes_auth import current_user
from app.models.db import Portfolio, Position, User, get_db
from app.services.analysis import analyze_stock

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class PositionIn(BaseModel):
    symbol: str
    exchange: str = "NSE"
    quantity: float
    avg_buy_price: float
    buy_date: date
    horizon: str | None = None


async def _get_or_create_portfolio(db: AsyncSession, user: User) -> Portfolio:
    pf = await db.scalar(select(Portfolio).where(Portfolio.user_id == user.id))
    if not pf:
        pf = Portfolio(user_id=user.id)
        db.add(pf)
        await db.commit()
        await db.refresh(pf)
    return pf


@router.post("/position", status_code=201)
async def add_position(body: PositionIn, db: AsyncSession = Depends(get_db),
                       user: User = Depends(current_user)):
    pf = await _get_or_create_portfolio(db, user)
    pos = Position(portfolio_id=pf.id, symbol=body.symbol.upper(),
                   exchange=body.exchange, quantity=body.quantity,
                   avg_buy_price=body.avg_buy_price, buy_date=body.buy_date,
                   horizon=body.horizon)
    db.add(pos)
    await db.commit()
    await db.refresh(pos)
    return {"id": str(pos.id), "symbol": pos.symbol}


@router.get("")
async def list_positions(db: AsyncSession = Depends(get_db),
                         user: User = Depends(current_user)):
    pf = await _get_or_create_portfolio(db, user)
    out = []
    for pos in pf.positions:
        analysis = await analyze_stock(pos.symbol, pos.exchange)
        ltp = analysis.get("indicators", {}).get("price")
        label = analysis.get("signal", {}).get("label")
        pnl = pnl_pct = None
        if ltp is not None:
            pnl = round((ltp - float(pos.avg_buy_price)) * float(pos.quantity), 2)
            pnl_pct = round((ltp / float(pos.avg_buy_price) - 1) * 100, 2)
        # Simple hold/sell hint from the live signal (advisory only)
        hint = "REVIEW"
        if label in ("STRONG_SELL", "SELL", "AVOID"):
            hint = "CONSIDER_EXIT"
        elif label in ("BUY", "STRONG_BUY", "HOLD"):
            hint = "HOLD"
        out.append({
            "id": str(pos.id), "symbol": pos.symbol, "quantity": float(pos.quantity),
            "avg_buy_price": float(pos.avg_buy_price), "ltp": ltp,
            "pnl": pnl, "pnl_pct": pnl_pct, "signal": label, "hint": hint,
        })
    return {"positions": out,
            "disclaimer": "Advisory only. Not investment advice. Trades are never auto-executed."}
