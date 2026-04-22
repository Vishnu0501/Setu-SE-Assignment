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