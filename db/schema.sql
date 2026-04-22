CREATE TABLE IF NOT EXISTS merchants (
    merchant_id   TEXT PRIMARY KEY,
    merchant_name TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id UUID        PRIMARY KEY,
    merchant_id    TEXT        NOT NULL REFERENCES merchants(merchant_id),
    amount         NUMERIC(12, 2) NOT NULL,
    currency       TEXT        NOT NULL DEFAULT 'INR',
    status         TEXT        NOT NULL DEFAULT 'initiated',
    created_at     TIMESTAMPTZ NOT NULL,
    updated_at     TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id       UUID        PRIMARY KEY,
    event_type     TEXT        NOT NULL,
    transaction_id UUID        NOT NULL REFERENCES transactions(transaction_id),
    merchant_id    TEXT        NOT NULL,
    amount         NUMERIC(12, 2),
    currency       TEXT,
    timestamp      TIMESTAMPTZ NOT NULL,
    received_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_merchant_id ON transactions(merchant_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status      ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at  ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_events_transaction_id    ON events(transaction_id);
CREATE INDEX IF NOT EXISTS idx_events_event_type        ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp         ON events(timestamp);