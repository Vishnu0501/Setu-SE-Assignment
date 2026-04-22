LIST_TRANSACTIONS_BASE = """
    SELECT t.*, m.merchant_name, COUNT(*) OVER() AS total_count
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
"""

GET_TRANSACTION_BY_ID = """
    SELECT t.*, m.merchant_name
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE t.transaction_id = $1
"""

GET_EVENTS_BY_TRANSACTION = """
    SELECT event_id, event_type, amount, currency, timestamp, received_at
    FROM events
    WHERE transaction_id = $1
    ORDER BY timestamp ASC
"""