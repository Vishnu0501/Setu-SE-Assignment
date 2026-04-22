from fastapi import APIRouter, Depends, HTTPException
from app.models.transaction import TransactionFilters
from app.database import get_db
from app.utils import serialize

router = APIRouter()

@router.get("/transactions")
def list_transactions(filters: TransactionFilters = Depends()):
    where_parts = []
    params = []

    if filters.merchant_id:
        where_parts.append("t.merchant_id = %s")
        params.append(filters.merchant_id)
    if filters.status:
        where_parts.append("t.status = %s")
        params.append(filters.status)
    if filters.from_date:
        where_parts.append("t.created_at >= %s")
        params.append(filters.from_date)
    if filters.to_date:
        where_parts.append("t.created_at <= %s")
        params.append(filters.to_date)
    
    where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
    order = f"t.{filters.sort_by} {filters.sort_order.upper()}"
    offset = (filters.page - 1) * filters.page_size

    query = f"""
    SELECT t.*, m.merchant_name, COUNT(*) OVER() AS total_count
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
   {where}
    ORDER BY {order}
    LIMIT %s OFFSET %s
    """
    params += [filters.page_size, offset]

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()

    total = int(rows[0]["total_count"]) if rows else 0
    data  = [serialize({k: v for k, v in row.items() if k != "total_count"}) for row in rows]

    return {
        "data": data,
        "pagination": {
            "page":        filters.page,
            "page_size":   filters.page_size,
            "total":       total,
            "total_pages": -(-total // filters.page_size),
            }
    }