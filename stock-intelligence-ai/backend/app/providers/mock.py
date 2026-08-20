"""Deterministic mock price provider.

Generates repeatable synthetic OHLCV so the full analysis pipeline runs and is
testable without any vendor account. Selected automatically when no real provider
keys are configured. NOT for production signals.
"""
from __future__ import annotations

import hashlib
import math
from datetime import datetime, timedelta, timezone

from app.providers.base import DataResult, PriceProvider


class MockPriceProvider(PriceProvider):
    name = "mock"

    def _seed(self, symbol: str) -> int:
        return int(hashlib.sha256(symbol.encode()).hexdigest(), 16) % 100_000

    async def get_quote(self, symbol: str, exchange: str) -> DataResult:
        base = 100 + (self._seed(symbol) % 2000)
        return DataResult(
            data={"symbol": symbol, "exchange": exchange, "ltp": round(base, 2)},
            source=self.name, is_delayed=True,
        )

    async def get_history(self, symbol, exchange, interval, start, end) -> DataResult:
        import random
        seed = self._seed(symbol)
        rng = random.Random(seed)                # deterministic per symbol
        base = 100 + (seed % 2000)
        mean = base
        price = base
        drift = ((seed % 7) - 3) * 0.0008         # small symbol-specific bias
        candles = []
        now = datetime.now(timezone.utc)
        # 120 daily candles: mean-reverting random walk -> realistic RSI/MACD ranges
        for i in range(120):
            t = now - timedelta(days=120 - i)
            reversion = (mean - price) * 0.05     # pull back toward mean
            shock = rng.gauss(0, base * 0.012)
            close = price + reversion + shock + drift * base
            openp = price + rng.gauss(0, base * 0.004)
            high = max(openp, close) + abs(rng.gauss(0, base * 0.005))
            low = min(openp, close) - abs(rng.gauss(0, base * 0.005))
            vol = 100_000 + rng.randint(0, 80_000) + int(abs(shock) * 400)
            candles.append([t.strftime("%Y-%m-%d %H:%M:%S"),
                            round(openp, 2), round(high, 2), round(low, 2),
                            round(close, 2), vol])
            price = close
        return DataResult(data=candles, source=self.name, is_delayed=True)
