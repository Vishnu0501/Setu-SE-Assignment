from fastapi import APIRouter, Depends
from app.models.reconciliation import SummaryFilters, DiscrepancyFilters
from app.database import get_db
from app.utils import serialize
from typing import Optional
router = APIRouter()

@router.get("/reconciliation/summary")
def reconciliation_summary(filters: SummaryFilters = Depends()):
    date_filter = ""
    params = []
    if filters.from_date:
        date_filter += " AND t.created_at >= %s"
        params.append(filters.from_date)
    if filters.to_date:
        date_filter += " AND t.created_at <= %s"
        params.append(filters.to_date)

    if filters.group_by == "merchant":
        query = f"""
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
    elif filters.group_by == "date":
        query = f"""
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
    else:  # status
        query = f"""
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
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
    return {"group_by": filters.group_by, "data": serialize(list(rows))}

@router.get("/reconciliation/discrepancies")
def reconciliation_discrepancies(filters: DiscrepancyFilters = Depends()):
    results = {}
    with get_db() as conn:
        cur = conn.cursor()
        if filters.type is None or filters.type == "processed_not_settled":
            cur.execute("""
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
            """)
            results["processed_not_settled"] = serialize(cur.fetchall())
        if filters.type is None or filters.type == "settled_after_failure":
            cur.execute("""
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
            """)
            results["settled_after_failure"] = serialize(cur.fetchall())
        if filters.type is None or filters.type == "conflicting_states":
            cur.execute("""
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
            """)
            results["conflicting_states"] = serialize(cur.fetchall())
    if filters.type:
        data = results.get(filters.type, [])
        return {"type": filters.type, "count": len(data), "data": data}
    return {
        "summary": {k: len(v) for k, v in results.items()},
        "data":    results,
    }