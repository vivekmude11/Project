# Architecture — Stock Intelligence AI

## 1. System overview

```
Android (Compose/MVVM/Clean)  --REST + WebSocket-->  FastAPI gateway
     |                                                    |
 Room/DataStore cache                          ┌──────────┴───────────┐
                                               │ Scoring engine (quant)│
                                               │ RAG + LLM reasoner     │
                                               │ Signal/portfolio svc   │
                                               └──────────┬───────────┘
                                            Data-provider abstraction (interface)
                                               ┌──────────┴───────────┐
                                               │ price · options · news│
                                               │ deals · fundamentals   │
                                               └──────────┬───────────┘
                        Ingestion workers (Celery/APScheduler): pull, dedupe, score
                                               |
                              PostgreSQL (+pgvector)   ·   Redis cache
                                               |
                        External: broker/vendor APIs · news APIs · LLM API
```

**Core rule:** the quant scoring engine sets the number; the LLM only explains it,
grounded on retrieved, timestamped data (RAG). This keeps price/signal logic
deterministic, testable and auditable, and keeps the LLM out of price prediction.

## 2. Data-source options (India + global)

The Indian market is more locked-down than the US: NSE/BSE license real-time data
through authorized vendors, so most APIs are either broker-dependent or via aggregators.

**Indian prices / F&O — pick a path:**
- *Path A (prototype / personal):* broker APIs. Angel One SmartAPI (free), Dhan
  (trading free, data ~₹499/mo), Upstox, Fyers (free), Zerodha Kite Connect (~₹2,000/mo).
  All offer WebSocket streaming. Redistributing broker data to many users is a grey area.
- *Path B (compliant public launch):* NSE/BSE/MCX **authorized data vendors** —
  **TrueData**, **Global Datafeeds**. Provide option chain, OI, greeks, historical,
  and corporate feeds. Data is licensed, not owned; **no resale/redistribution** without
  agreement; several vendors **disallow simulation/virtual-trading use** without approval.

**Options chain / OI / greeks:** TrueData, Global Datafeeds, or broker APIs.

**Fundamentals, corporate announcements, bulk/block deals:** Global Datafeeds corporate
feed (announcements, actions, shareholding, results, promoter pledge, bulk/block deals,
sectoral classification); plus official NSE/BSE published data. Never scrape protected pages.

**Global markets (US/EU/Asia indices, forex, commodities, yields, DXY, USD/INR, crude,
gold):** Alpha Vantage, Finnhub, Twelve Data, Polygon (US depth), FMP.

**News + sentiment:** Alpha Vantage News & Sentiment (large ticker universe), Marketaux
(broad entity/market coverage), Finnhub; NewsData.io/GNews for general news. Layer
official NSE/BSE/SEBI/RBI announcements for authoritative signals. Sentiment scores are
**not comparable across vendors** — normalize everything through the app's own scoring layer.

**Recommended start:** Angel One SmartAPI (or Dhan) + Alpha Vantage + Marketaux + Finnhub,
behind the provider interface so migrating to TrueData/Global Datafeeds is a config change.

> Verify current pricing and free-tier limits with each provider before committing —
> plans change frequently.

## 3. Hybrid scoring (spec §8)

`final = Σ weightᵢ · subscoreᵢ`, each sub-score normalized to [−100, 100], weights
versioned and configurable (`app/scoring/weights.py`). Default blend:

| Factor | Weight |
|---|---|
| Technical | 0.20 |
| Fundamental | 0.15 |
| News sentiment | 0.15 |
| Market sentiment | 0.15 |
| Institutional (FII/DII + deals) | 0.10 |
| Options | 0.10 |
| Global market | 0.10 |
| Other (volatility/risk) | 0.05 |

Label bands: STRONG_BUY ≥60, BUY ≥25, HOLD (−25,25), AVOID (−45,−25], SELL (−60,−45],
STRONG_SELL ≤−60. **Confidence** blends sub-score agreement, signal magnitude, and
(when available) the calibrated historical hit-rate for the active weight-set — so a
"70%" is tied to real out-of-sample performance, not a profit promise.

## 4. API contract (target)

```
GET  /health
POST /score                        # demo: sub-scores -> signal (live in M1)
GET  /market/global
GET  /market/india
GET  /stock/{symbol}
GET  /stock/{symbol}/analysis
GET  /stock/{symbol}/news
GET  /stock/{symbol}/signals
GET  /market/bulk-deals
GET  /market/block-deals
GET  /market/options/{symbol}
POST /portfolio
POST /portfolio/position
POST /ai/chat
GET  /signals
GET  /signals/performance
WS   /ws/live                      # ticks + fresh signals
```

Every AI response carries: data timestamp, sources, confidence, risk warning, disclaimer.

## 5. Android screens

Bottom nav: **Home · Markets · Discover · Portfolio · AI Chat** (dark theme).
- Home: global + India sentiment gauges, NIFTY/BANKNIFTY, top signals, FII/DII, news, watchlist.
- Markets: India (indices/breadth/VIX/sector heatmap) and Global (indices/yields/crude/gold/DXY/USD-INR).
- Discover: screeners, bulk/block deals, options dashboard (OI/PCR/max pain).
- Stock detail: header → AI recommendation (label/confidence/entry/targets/SL/RR) → "Why this signal?" →
  technicals → fundamentals → news sentiment → institutional activity → chart → risk.
- AI Chat: RAG-grounded; each answer shows sources + timestamp + confidence + risk.
- Portfolio: positions with live P/L, suggested SL/target, hold/sell, alerts.

## 6. Security (spec §16)

JWT auth (access + refresh), secrets only via env vars, HTTPS, per-user + per-IP rate
limiting, Pydantic input validation, parameterized queries (SQLAlchemy) to prevent
injection, structured logging + error monitoring. No API keys in source or client app.
