"""Provider abstraction (spec section 15).

Every external data source implements one of these interfaces. Business logic
depends only on the interface, so swapping Angel One -> TrueData is a config
change. Each result carries a `fetched_at` freshness stamp. A FallbackProvider
tries providers in order and returns the first success.

Compliance reminder: exchange data is LICENSED, not owned. Respect your vendor's
redistribution terms and never bypass auth/CAPTCHA/rate-limit protections.
"""
from __future__ import annotations

import abc
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class DataResult:
    data: Any
    source: str
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_delayed: bool = False


class ProviderError(Exception):
    pass


class RateLimitError(ProviderError):
    pass


class PriceProvider(abc.ABC):
    name: str = "abstract"

    @abc.abstractmethod
    async def get_quote(self, symbol: str, exchange: str) -> DataResult: ...

    @abc.abstractmethod
    async def get_history(self, symbol: str, exchange: str, interval: str,
                          start: datetime, end: datetime) -> DataResult: ...


class OptionsProvider(abc.ABC):
    name: str = "abstract"

    @abc.abstractmethod
    async def get_option_chain(self, underlying: str, expiry: Optional[str] = None) -> DataResult: ...


class NewsProvider(abc.ABC):
    name: str = "abstract"

    @abc.abstractmethod
    async def get_news(self, symbols: Optional[list[str]] = None, limit: int = 50) -> DataResult: ...


class DealsProvider(abc.ABC):
    name: str = "abstract"

    @abc.abstractmethod
    async def get_bulk_deals(self, date: Optional[str] = None) -> DataResult: ...

    @abc.abstractmethod
    async def get_block_deals(self, date: Optional[str] = None) -> DataResult: ...


async def with_retry(coro_factory, *, attempts: int = 3, base_delay: float = 0.5):
    """Retry with exponential backoff. `coro_factory` is a zero-arg callable
    returning a fresh awaitable each attempt."""
    last_exc: Optional[Exception] = None
    for i in range(attempts):
        try:
            return await coro_factory()
        except RateLimitError as e:
            last_exc = e
            await asyncio.sleep(base_delay * (2 ** i) * 2)   # back off harder on 429
        except ProviderError as e:
            last_exc = e
            await asyncio.sleep(base_delay * (2 ** i))
    raise last_exc if last_exc else ProviderError("retry failed")


class FallbackProvider:
    """Wraps an ordered list of same-interface providers. Returns the first that
    succeeds; logs and continues on failure."""

    def __init__(self, providers: list[Any], method: str):
        if not providers:
            raise ValueError("FallbackProvider needs at least one provider")
        self._providers = providers
        self._method = method

    async def __call__(self, *args, **kwargs) -> DataResult:
        errors = []
        for p in self._providers:
            try:
                fn = getattr(p, self._method)
                return await with_retry(lambda: fn(*args, **kwargs))
            except Exception as e:               # noqa: BLE001 — deliberate fallthrough
                logger.warning("Provider %s failed on %s: %s", p.name, self._method, e)
                errors.append(f"{p.name}: {e}")
        raise ProviderError(f"All providers failed for {self._method}: {errors}")
