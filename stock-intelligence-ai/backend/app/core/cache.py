"""Cache layer with freshness tracking.

Uses Redis when reachable; falls back to an in-process dict so the app runs in
dev/test without Redis. Every cached market payload stores a fetched_at timestamp
so the API and UI can always show "data as of ...".
"""
from __future__ import annotations

import json
import time
from typing import Any, Optional

from app.core.config import get_settings

try:
    import redis.asyncio as aioredis
except ImportError:  # pragma: no cover
    aioredis = None


class Cache:
    def __init__(self):
        self._settings = get_settings()
        self._redis = None
        self._mem: dict[str, tuple[float, str]] = {}   # key -> (expires_at, json)

    async def _client(self):
        if aioredis is None:
            return None
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(self._settings.redis_url,
                                                decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        r = await self._client()
        if r is not None:
            raw = await r.get(key)
            return json.loads(raw) if raw else None
        # memory fallback
        item = self._mem.get(key)
        if not item:
            return None
        expires, raw = item
        if expires < time.time():
            self._mem.pop(key, None)
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int = 60) -> None:
        raw = json.dumps(value, default=str)
        r = await self._client()
        if r is not None:
            await r.set(key, raw, ex=ttl)
        else:
            self._mem[key] = (time.time() + ttl, raw)


_cache: Optional[Cache] = None


def get_cache() -> Cache:
    global _cache
    if _cache is None:
        _cache = Cache()
    return _cache
