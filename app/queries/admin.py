UPSERT_MERCHANT_SEED = """
    INSERT INTO merchants (merchant_id, merchant_name)
    VALUES ($1, $2)
    ON CONFLICT (merchant_id) DO NOTHING
"""

UPSERT_TRANSACTION_SEED = """
    INSERT INTO transactions
        (transaction_id, merchant_id, amount, currency, status, created_at, updated_at)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    ON CONFLICT (transaction_id) DO UPDATE SET
        status     = CASE WHEN transactions.updated_at < EXCLUDED.updated_at
                     THEN EXCLUDED.status ELSE transactions.status END,
        updated_at = GREATEST(transactions.updated_at, EXCLUDED.updated_at)
"""

INSERT_EVENT_SEED = """
    INSERT INTO events
        (event_id, event_type, transaction_id, merchant_id, amount, currency, timestamp)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    ON CONFLICT (event_id) DO NOTHING
"""