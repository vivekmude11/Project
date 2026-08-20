"""Async SQLAlchemy setup + ORM models (subset used by the API in M4).

Models map onto db/schema.sql. Only the tables the current API touches are defined
as ORM classes; the rest of the schema is created by schema.sql. Uses UUID PKs and
async sessions. Requires the Postgres from docker-compose to actually run.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import ForeignKey, Numeric, String, Date, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.config import get_settings

_settings = get_settings()
engine = create_async_engine(_settings.database_url, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    risk_profile: Mapped[str] = mapped_column(String, default="MODERATE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())


class Portfolio(Base):
    __tablename__ = "portfolio"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                               ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String, default="My Portfolio")
    positions: Mapped[list["Position"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan", lazy="selectin")


class Position(Base):
    __tablename__ = "portfolio_positions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio.id", ondelete="CASCADE"))
    symbol: Mapped[str] = mapped_column(String)          # denormalized for convenience
    exchange: Mapped[str] = mapped_column(String, default="NSE")
    quantity: Mapped[float] = mapped_column(Numeric(18, 4))
    avg_buy_price: Mapped[float] = mapped_column(Numeric(14, 2))
    buy_date: Mapped[date] = mapped_column(Date)
    horizon: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="OPEN")
    portfolio: Mapped["Portfolio"] = relationship(back_populates="positions")


async def get_db() -> AsyncSession:  # FastAPI dependency
    async with SessionLocal() as session:
        yield session
