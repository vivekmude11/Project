# Stock Intelligence AI

An AI-based stock market **analysis and research** tool for Indian markets. It blends
global + Indian market data, NSE/BSE data, bulk/block deals, corporate announcements,
news sentiment, technical indicators and options data into a hybrid quantitative score,
and produces BUY / SELL / HOLD signals with confidence, entry/target/stop-loss and
plain-language reasoning.

> **Want the APK?** See [`GET_YOUR_APK.md`](GET_YOUR_APK.md). The fastest path (no local
> setup) is pushing to GitHub — the included Actions workflow builds an installable
> debug APK and hands it back as a downloadable artifact.

> **Disclaimer.** This is an AI-based analysis and research tool. It does **not**
> guarantee profit or accuracy. It is **not** SEBI-registered financial advice unless
> all applicable legal and regulatory requirements are met. Users must make their own
> investment decisions. No guaranteed returns or "100% accurate" predictions are claimed.

## Regulatory note (read before distributing signals)

In India, issuing buy/sell/hold recommendations on **specific securities** to others
"for consideration" is governed by the SEBI (Research Analysts) Regulations, 2014
(amended 2024; FAQs 2025), including a mandatory disclosure of AI use. General
market/index/sector commentary is excluded, but specific-stock signals are not.
A single-user tool for your own decisions differs from distributing signals to many
users. **Get qualified legal advice and, if required, SEBI RA registration before any
commercial distribution.** This project is not legal advice.

## Data licensing note

Exchange market data is **licensed, not owned**; redistribution/resale is governed by
your vendor and exchange/SEBI agreements. Some authorized vendors also restrict data
use for **simulation / virtual-trading / backtesting** without prior approval — plan
the paper-trading module accordingly. Never scrape protected NSE/BSE pages or bypass
auth/CAPTCHA/rate-limit controls.

## Repository layout

```
stock-intelligence-ai/
├── README.md
├── docs/ARCHITECTURE.md         # architecture, data sources, screens, plan
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app (health + demo /score)
│   │   ├── core/config.py       # env-based config, no hardcoded secrets
│   │   ├── scoring/             # hybrid scoring engine (deterministic, quant)
│   │   ├── providers/base.py    # data-provider interface + fallback/retry
│   │   ├── api/ models/ services/  # (filled in M2+)
│   ├── db/schema.sql            # full PostgreSQL schema (+ pgvector)
│   ├── docker-compose.yml       # api + postgres(pgvector) + redis
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
└── android/                     # (added in M7) Kotlin · Compose · Material 3
```

## Quick start (backend)

Requires Docker.

```bash
cd backend
cp .env.example .env
# edit .env: set a strong JWT_SECRET and any provider keys you have
docker compose up --build
```

Then:

```bash
curl http://localhost:8000/health

# Full AI analysis for a stock (runs on mock data until you add provider keys)
curl "http://localhost:8000/stock/RELIANCE/analysis?hit_rate=0.7"

# Lightweight summary
curl "http://localhost:8000/stock/INFY"

# Register + login (returns a JWT)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","password":"s3cret"}'
```

Interactive API docs: http://localhost:8000/docs

### Endpoints live now

| Method | Path | Notes |
|---|---|---|
| GET  | `/health` | liveness |
| POST | `/score` | raw sub-scores → signal (demo) |
| GET  | `/stock/{symbol}/analysis` | indicators + signal + freshness |
| GET  | `/stock/{symbol}` | price + label summary |
| POST | `/auth/register`, `/auth/login` | JWT auth |
| POST | `/portfolio/position` | add a position (auth) |
| GET  | `/portfolio` | positions with live P/L + hold/sell hint (auth) |

### Using real Angel One data instead of mock

Install the SDK and set credentials — the app auto-switches from mock to Angel One
when all four are present (mock stays as fallback):

```bash
pip install smartapi-python pyotp
# in .env:
ANGELONE_API_KEY=...        ANGELONE_CLIENT_ID=...
ANGELONE_PIN=...            ANGELONE_TOTP_SECRET=...   # QR/TOTP secret from enable-totp
```

Get keys at the SmartAPI developer portal; enable TOTP at
`smartapi.angelbroking.com/enable-totp`. Angel One SmartAPI is free.

### Run the scoring engine directly (no server)

```bash
cd backend && python -m app.scoring.engine
```

## Roadmap (milestones)

- **M1 (done):** architecture, schema, scoring engine, Docker, README.
- **M2:** provider adapters (Angel One/Dhan prices, Alpha Vantage global + news), Redis cache.
- **M3:** indicators + news dedupe/classification wired into scoring → `/stock/{symbol}/analysis`, `/signals`.
- **M4:** JWT auth, portfolio/position monitor, alerts, FCM push.
- **M5:** RAG + grounded LLM chat.
- **M6:** signal-performance tracking + backtesting/paper trading.
- **M7–M8:** Android app (Compose) + WebSocket live updates.
- **M9:** full test suite incl. failure scenarios.
- **M10:** build/CI + APK/AAB signing instructions.
