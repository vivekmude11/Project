"""Angel One SmartAPI price adapter.

Implements PriceProvider against angel-one/smartapi-python. The SDK is synchronous
(requests-based), so blocking calls run in a thread via asyncio.to_thread to fit the
async interface. Auth uses client code + MPIN/PIN + TOTP (pyotp) per SmartAPI:

    smartApi = SmartConnect(api_key)
    totp = pyotp.TOTP(totp_secret).now()
    session = smartApi.generateSession(client_code, pin, totp)   # -> jwtToken/refreshToken
    smartApi.getCandleData({exchange, symboltoken, interval, fromdate, todate})
    # each candle: [timestamp, open, high, low, close, volume]

Symbol -> symboltoken resolution uses the instrument master JSON Angel publishes.
Install: pip install smartapi-python pyotp
Set env: ANGELONE_API_KEY, ANGELONE_CLIENT_ID, ANGELONE_PIN, ANGELONE_TOTP_SECRET
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from app.providers.base import DataResult, PriceProvider, ProviderError, RateLimitError

logger = logging.getLogger(__name__)

_INSTRUMENT_URL = (
    "https://margincalculator.angelbroking.com/OpenAPI_File/files/"
    "OpenAPIScripMaster.json"
)

_INTERVAL_MAP = {
    "1m": "ONE_MINUTE", "5m": "FIVE_MINUTE", "15m": "FIFTEEN_MINUTE",
    "30m": "THIRTY_MINUTE", "1h": "ONE_HOUR", "1d": "ONE_DAY",
}


class AngelOneProvider(PriceProvider):
    name = "angelone"

    def __init__(self, api_key: str, client_id: str, pin: str, totp_secret: str):
        self._api_key = api_key
        self._client_id = client_id
        self._pin = pin
        self._totp_secret = totp_secret
        self._smart = None                     # SmartConnect instance
        self._instruments: dict[str, str] = {}  # "NSE:RELIANCE-EQ" -> token
        self._lock = asyncio.Lock()

    async def _ensure_session(self):
        if self._smart is not None:
            return
        async with self._lock:
            if self._smart is not None:
                return
            try:
                from SmartApi import SmartConnect   # lazy import
                import pyotp
            except ImportError as e:  # pragma: no cover
                raise ProviderError(
                    "smartapi-python/pyotp not installed. `pip install smartapi-python pyotp`"
                ) from e

            def _login():
                smart = SmartConnect(self._api_key)
                totp = pyotp.TOTP(self._totp_secret).now()
                res = smart.generateSession(self._client_id, self._pin, totp)
                if not res or not res.get("status"):
                    raise ProviderError(f"Angel One login failed: {res}")
                return smart

            self._smart = await asyncio.to_thread(_login)
            await self._load_instruments()

    async def _load_instruments(self):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(_INSTRUMENT_URL)
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            logger.warning("Instrument master load failed: %s", e)
            return
        for row in data:
            exch = row.get("exch_seg")
            sym = row.get("symbol")            # e.g. RELIANCE-EQ
            token = row.get("token")
            if exch and sym and token:
                self._instruments[f"{exch}:{sym}"] = token

    def _resolve_token(self, symbol: str, exchange: str) -> str:
        # symbol like "RELIANCE" -> "RELIANCE-EQ" for equities
        key = f"{exchange}:{symbol}-EQ"
        token = self._instruments.get(key) or self._instruments.get(f"{exchange}:{symbol}")
        if not token:
            raise ProviderError(f"Symbol token not found for {exchange}:{symbol}")
        return token

    async def get_quote(self, symbol: str, exchange: str) -> DataResult:
        await self._ensure_session()
        token = self._resolve_token(symbol, exchange)

        def _ltp():
            return self._smart.ltpData(exchange, f"{symbol}-EQ", token)

        try:
            res = await asyncio.to_thread(_ltp)
        except Exception as e:
            self._raise_mapped(e)
        if not res or not res.get("status"):
            raise ProviderError(f"ltpData failed: {res}")
        return DataResult(data=res["data"], source=self.name)

    async def get_history(self, symbol, exchange, interval, start, end) -> DataResult:
        await self._ensure_session()
        token = self._resolve_token(symbol, exchange)
        ang_interval = _INTERVAL_MAP.get(interval, "ONE_DAY")
        params = {
            "exchange": exchange,
            "symboltoken": token,
            "interval": ang_interval,
            "fromdate": start.strftime("%Y-%m-%d %H:%M"),
            "todate": end.strftime("%Y-%m-%d %H:%M"),
        }

        def _candles():
            return self._smart.getCandleData(params)

        try:
            res = await asyncio.to_thread(_candles)
        except Exception as e:
            self._raise_mapped(e)
        if not res or not res.get("status"):
            raise ProviderError(f"getCandleData failed: {res}")
        return DataResult(data=res["data"], source=self.name)

    @staticmethod
    def _raise_mapped(e: Exception):
        msg = str(e).lower()
        if "rate" in msg or "429" in msg or "access" in msg and "denied" in msg:
            raise RateLimitError(str(e)) from e
        raise ProviderError(str(e)) from e
