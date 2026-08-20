"""Provider registry — picks the active price provider from config.

Angel One is used when all its credentials are present; otherwise the mock provider
keeps the pipeline runnable. Wrapped in FallbackProvider so you can chain multiple
real providers later (e.g. Angel One -> Dhan) without touching services.
"""
from __future__ import annotations

import os
from functools import lru_cache

from app.core.config import get_settings
from app.providers.base import FallbackProvider
from app.providers.mock import MockPriceProvider


@lru_cache
def price_provider_chain() -> list:
    s = get_settings()
    providers = []
    if s.angelone_api_key and s.angelone_client_id and os.getenv("ANGELONE_PIN") \
            and os.getenv("ANGELONE_TOTP_SECRET"):
        from app.providers.angelone import AngelOneProvider
        providers.append(AngelOneProvider(
            api_key=s.angelone_api_key,
            client_id=s.angelone_client_id,
            pin=os.getenv("ANGELONE_PIN", ""),
            totp_secret=os.getenv("ANGELONE_TOTP_SECRET", ""),
        ))
    providers.append(MockPriceProvider())      # always last-resort fallback
    return providers


def get_history_fn():
    return FallbackProvider(price_provider_chain(), "get_history")


def get_quote_fn():
    return FallbackProvider(price_provider_chain(), "get_quote")
