SUMMARY_BY_MERCHANT = """
    SELECT
        t.merchant_id,
        m.merchant_name,
        COUNT(*)                                                        AS total_transactions,
        SUM(t.amount)                                                   AS total_amount,
        SUM(CASE WHEN t.status = 'settled'   THEN 1 ELSE 0 END)        AS settled_count,
        SUM(CASE WHEN t.status = 'processed' THEN 1 ELSE 0 END)        AS processed_count,
        SUM(CASE WHEN t.status = 'failed'    THEN 1 ELSE 0 END)        AS failed_count,
        SUM(CASE WHEN t.status = 'initiated' THEN 1 ELSE 0 END)        AS initiated_count,
        SUM(CASE WHEN t.status = 'settled'   THEN t.amount ELSE 0 END) AS settled_amount
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE 1=1 {date_filter}
    GROUP BY t.merchant_id, m.merchant_name
    ORDER BY total_amount DESC
"""

SUMMARY_BY_DATE = """
    SELECT
        DATE(t.created_at)                                              AS date,
        COUNT(*)                                                        AS total_transactions,
        SUM(t.amount)                                                   AS total_amount,
        SUM(CASE WHEN t.status = 'settled'   THEN 1 ELSE 0 END)        AS settled_count,
        SUM(CASE WHEN t.status = 'processed' THEN 1 ELSE 0 END)        AS processed_count,
        SUM(CASE WHEN t.status = 'failed'    THEN 1 ELSE 0 END)        AS failed_count,
        SUM(CASE WHEN t.status = 'settled'   THEN t.amount ELSE 0 END) AS settled_amount
    FROM transactions t
    WHERE 1=1 {date_filter}
    GROUP BY DATE(t.created_at)
    ORDER BY date DESC
"""

SUMMARY_BY_STATUS = """
    SELECT
        t.status,
        COUNT(*)                      AS total_transactions,
        SUM(t.amount)                 AS total_amount,
        COUNT(DISTINCT t.merchant_id) AS merchant_count
    FROM transactions t
    WHERE 1=1 {date_filter}
    GROUP BY t.status
    ORDER BY total_transactions DESC
"""

DISCREPANCY_PROCESSED_NOT_SETTLED = """
    SELECT t.transaction_id, t.merchant_id, m.merchant_name,
           t.amount, t.currency, t.status, t.created_at, t.updated_at,
           'processed_not_settled' AS discrepancy_type
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE t.status = 'processed'
      AND NOT EXISTS (
          SELECT 1 FROM events e
          WHERE e.transaction_id = t.transaction_id
            AND e.event_type = 'settled'
      )
    ORDER BY t.updated_at DESC
"""

DISCREPANCY_SETTLED_AFTER_FAILURE = """
    SELECT t.transaction_id, t.merchant_id, m.merchant_name,
           t.amount, t.currency, t.status, t.created_at, t.updated_at,
           'settled_after_failure' AS discrepancy_type
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE EXISTS (
              SELECT 1 FROM events e
              WHERE e.transaction_id = t.transaction_id
                AND e.event_type = 'settled'
          )
      AND EXISTS (
              SELECT 1 FROM events e
              WHERE e.transaction_id = t.transaction_id
                AND e.event_type = 'payment_failed'
          )
    ORDER BY t.updated_at DESC
"""

DISCREPANCY_CONFLICTING_STATES = """
    SELECT t.transaction_id, t.merchant_id, m.merchant_name,
           t.amount, t.currency, t.status, t.created_at, t.updated_at,
           'conflicting_states' AS discrepancy_type
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE EXISTS (
              SELECT 1 FROM events e
              WHERE e.transaction_id = t.transaction_id
                AND e.event_type = 'payment_processed'
          )
      AND EXISTS (
              SELECT 1 FROM events e
              WHERE e.transaction_id = t.transaction_id
                AND e.event_type = 'payment_failed'
          )
    ORDER BY t.updated_at DESC
"""