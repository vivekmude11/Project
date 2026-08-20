-- Stock Intelligence AI — PostgreSQL schema
-- Requires: PostgreSQL 16+, extension "pgvector" for RAG.
-- All monetary values stored in the smallest sensible precision; prices as NUMERIC.
-- NOTE: Market data stored here is licensed from exchanges/vendors, not owned.
--       Redistribution is governed by your vendor + SEBI/exchange agreements.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "vector";     -- pgvector for RAG embeddings

-- ---------- ENUM TYPES ----------
CREATE TYPE signal_label     AS ENUM ('STRONG_BUY','BUY','HOLD','AVOID','SELL','STRONG_SELL');
CREATE TYPE sentiment_label  AS ENUM ('VERY_BULLISH','BULLISH','NEUTRAL','BEARISH','VERY_BEARISH');
CREATE TYPE deal_side        AS ENUM ('BUY','SELL');
CREATE TYPE position_status  AS ENUM ('OPEN','PARTIAL','CLOSED');
CREATE TYPE alert_type       AS ENUM ('STRONG_BUY','STRONG_SELL','TARGET_HIT','STOPLOSS_WARN',
                                      'NEWS_EVENT','BULK_DEAL','ABNORMAL_VOLUME','FII_DII_CHANGE',
                                      'MARKET_CRASH','HIGH_VOLATILITY');
CREATE TYPE time_horizon     AS ENUM ('INTRADAY','SHORT','MEDIUM','LONG');
CREATE TYPE exchange_code     AS ENUM ('NSE','BSE');

-- ---------- USERS ----------
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           CITEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    display_name    TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    risk_profile    TEXT DEFAULT 'MODERATE',      -- CONSERVATIVE/MODERATE/AGGRESSIVE
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- INSTRUMENTS ----------
CREATE TABLE stocks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol          TEXT NOT NULL,                -- e.g. RELIANCE
    exchange        exchange_code NOT NULL,
    isin            TEXT,
    company_name    TEXT NOT NULL,
    sector          TEXT,
    industry        TEXT,
    lot_size        INTEGER,
    is_fno          BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (symbol, exchange)
);
CREATE INDEX idx_stocks_symbol ON stocks (symbol);
CREATE INDEX idx_stocks_sector ON stocks (sector);

-- ---------- PRICES ----------
CREATE TABLE market_prices (               -- latest / streaming snapshot
    stock_id        UUID PRIMARY KEY REFERENCES stocks(id) ON DELETE CASCADE,
    ltp             NUMERIC(14,2),
    open            NUMERIC(14,2),
    high            NUMERIC(14,2),
    low             NUMERIC(14,2),
    prev_close      NUMERIC(14,2),
    change_pct      NUMERIC(8,4),
    volume          BIGINT,
    delivery_pct    NUMERIC(6,3),           -- only where legally available
    data_source     TEXT,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now()   -- data freshness stamp
);

CREATE TABLE historical_prices (           -- OHLCV time-series
    id              BIGSERIAL PRIMARY KEY,
    stock_id        UUID NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    ts              TIMESTAMPTZ NOT NULL,
    interval        TEXT NOT NULL,          -- 1m/5m/15m/1d etc.
    open            NUMERIC(14,2),
    high            NUMERIC(14,2),
    low             NUMERIC(14,2),
    close           NUMERIC(14,2),
    volume          BIGINT,
    UNIQUE (stock_id, interval, ts)
);
CREATE INDEX idx_hist_stock_ts ON historical_prices (stock_id, interval, ts DESC);

-- ---------- NEWS + SENTIMENT ----------
CREATE TABLE news_articles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id     TEXT,                   -- vendor id for dedupe
    source          TEXT,                   -- e.g. Marketaux, NSE, RBI
    source_reliability NUMERIC(4,3),        -- 0..1 credibility weight
    url             TEXT,
    title           TEXT NOT NULL,
    summary         TEXT,
    dedupe_hash     TEXT UNIQUE,            -- hash(title+source+day) to drop dups
    published_at    TIMESTAMPTZ,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_news_published ON news_articles (published_at DESC);

CREATE TABLE news_sentiment (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    news_id         UUID NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
    stock_id        UUID REFERENCES stocks(id) ON DELETE SET NULL,  -- nullable: sector/macro news
    sector          TEXT,
    label           sentiment_label NOT NULL,
    score           NUMERIC(6,2) NOT NULL,   -- normalized -100..100
    is_high_impact  BOOLEAN NOT NULL DEFAULT FALSE,
    already_priced_in BOOLEAN,               -- model estimate
    model_version   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_newssent_stock ON news_sentiment (stock_id, created_at DESC);

-- ---------- DEALS ----------
CREATE TABLE bulk_deals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_id        UUID REFERENCES stocks(id) ON DELETE SET NULL,
    deal_date       DATE NOT NULL,
    client_name     TEXT,
    side            deal_side NOT NULL,
    quantity        BIGINT,
    price           NUMERIC(14,2),
    exchange        exchange_code,
    data_source     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_bulk_stock_date ON bulk_deals (stock_id, deal_date DESC);

CREATE TABLE block_deals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_id        UUID REFERENCES stocks(id) ON DELETE SET NULL,
    deal_date       DATE NOT NULL,
    client_name     TEXT,
    side            deal_side NOT NULL,
    quantity        BIGINT,
    price           NUMERIC(14,2),
    exchange        exchange_code,
    data_source     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_block_stock_date ON block_deals (stock_id, deal_date DESC);

CREATE TABLE corporate_announcements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_id        UUID REFERENCES stocks(id) ON DELETE CASCADE,
    category        TEXT,                   -- results/dividend/board meeting etc.
    headline        TEXT NOT NULL,
    detail          TEXT,
    announced_at    TIMESTAMPTZ,
    data_source     TEXT,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_corp_stock ON corporate_announcements (stock_id, announced_at DESC);

-- ---------- ANALYTICS INPUTS ----------
CREATE TABLE technical_indicators (
    stock_id        UUID PRIMARY KEY REFERENCES stocks(id) ON DELETE CASCADE,
    ema20 NUMERIC(14,2), ema50 NUMERIC(14,2), ema200 NUMERIC(14,2),
    rsi NUMERIC(6,2), macd NUMERIC(10,4), macd_signal NUMERIC(10,4),
    bb_upper NUMERIC(14,2), bb_lower NUMERIC(14,2), vwap NUMERIC(14,2),
    support NUMERIC(14,2), resistance NUMERIC(14,2),
    trend TEXT,                              -- UP/DOWN/SIDEWAYS
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE fundamental_data (
    stock_id        UUID PRIMARY KEY REFERENCES stocks(id) ON DELETE CASCADE,
    revenue_growth NUMERIC(8,4), profit_growth NUMERIC(8,4), eps_growth NUMERIC(8,4),
    pe NUMERIC(10,2), pb NUMERIC(10,2), roe NUMERIC(8,4), roce NUMERIC(8,4),
    debt_to_equity NUMERIC(8,4), operating_margin NUMERIC(8,4), net_margin NUMERIC(8,4),
    promoter_holding NUMERIC(6,3), promoter_pledge NUMERIC(6,3),
    institutional_holding NUMERIC(6,3),
    as_of DATE,
    data_source TEXT,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE options_data (
    id              BIGSERIAL PRIMARY KEY,
    underlying_id   UUID NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    expiry          DATE NOT NULL,
    strike          NUMERIC(14,2) NOT NULL,
    option_type     CHAR(2) NOT NULL,        -- CE / PE
    oi              BIGINT, oi_change BIGINT,
    iv              NUMERIC(8,4),
    ltp             NUMERIC(14,2),
    volume          BIGINT,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (underlying_id, expiry, strike, option_type, fetched_at)
);
CREATE INDEX idx_opt_underlying ON options_data (underlying_id, expiry);

-- ---------- SIGNALS ----------
CREATE TABLE ai_signals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_id        UUID NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    label           signal_label NOT NULL,
    final_score     NUMERIC(6,2) NOT NULL,   -- -100..100
    confidence      NUMERIC(5,2) NOT NULL,   -- 0..100 (calibrated)
    entry_price     NUMERIC(14,2),
    target1         NUMERIC(14,2),
    target2         NUMERIC(14,2),
    stop_loss       NUMERIC(14,2),
    risk_reward     NUMERIC(6,2),
    horizon         time_horizon,
    subscores       JSONB NOT NULL,          -- {technical, fundamental, news, ...}
    reasons         JSONB NOT NULL,          -- ["Strong quarterly results", ...]
    weights_version TEXT NOT NULL,
    model_version   TEXT NOT NULL,
    valid_until     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_signals_stock ON ai_signals (stock_id, created_at DESC);
CREATE INDEX idx_signals_created ON ai_signals (created_at DESC);

CREATE TABLE signal_performance (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id       UUID NOT NULL REFERENCES ai_signals(id) ON DELETE CASCADE,
    evaluated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    outcome         TEXT,                    -- TARGET_HIT/STOPPED/EXPIRED/OPEN
    realized_return NUMERIC(8,4),
    hit_target1     BOOLEAN,
    hit_target2     BOOLEAN,
    hit_stoploss    BOOLEAN,
    max_favorable   NUMERIC(8,4),
    max_adverse     NUMERIC(8,4)
);
CREATE INDEX idx_perf_signal ON signal_performance (signal_id);

-- ---------- PORTFOLIO / WATCHLIST ----------
CREATE TABLE portfolio (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL DEFAULT 'My Portfolio',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE portfolio_positions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id    UUID NOT NULL REFERENCES portfolio(id) ON DELETE CASCADE,
    stock_id        UUID NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    quantity        NUMERIC(18,4) NOT NULL,
    avg_buy_price   NUMERIC(14,2) NOT NULL,
    buy_date        DATE NOT NULL,
    horizon         time_horizon,
    status          position_status NOT NULL DEFAULT 'OPEN',
    trailing_sl     NUMERIC(14,2),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_pos_portfolio ON portfolio_positions (portfolio_id);

CREATE TABLE watchlist (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL DEFAULT 'Watchlist',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE watchlist_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    watchlist_id    UUID NOT NULL REFERENCES watchlist(id) ON DELETE CASCADE,
    stock_id        UUID NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    added_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (watchlist_id, stock_id)
);

-- ---------- ALERTS / NOTIFICATIONS ----------
CREATE TABLE alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stock_id        UUID REFERENCES stocks(id) ON DELETE CASCADE,
    type            alert_type NOT NULL,
    condition       JSONB,                   -- e.g. {"price_below": 1210}
    is_enabled      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_alerts_user ON alerts (user_id);

CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    body            TEXT,
    type            alert_type,
    payload         JSONB,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_notif_user ON notifications (user_id, created_at DESC);

-- ---------- AI CHAT ----------
CREATE TABLE chat_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,           -- user / assistant
    content         TEXT NOT NULL,
    sources         JSONB,                   -- retrieved doc refs for grounding
    data_timestamp  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_chat_user ON chat_history (user_id, created_at);

-- ---------- RAG VECTOR STORE ----------
CREATE TABLE rag_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_type        TEXT NOT NULL,           -- news/announcement/fundamental/technical
    stock_id        UUID REFERENCES stocks(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    embedding       VECTOR(1536),            -- match your embedding model dim
    source          TEXT,
    data_timestamp  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_rag_embedding ON rag_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_rag_stock ON rag_documents (stock_id);
