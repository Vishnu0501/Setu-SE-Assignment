from fastapi import APIRouter, HTTPException, Depends
from app.models.transaction import TransactionFilters
from app.database import db
from app import queries

router = APIRouter()


def _build_list_query(filters: TransactionFilters):
    """Build parameterized list query from filters. Returns (query_str, params)."""
    where_parts = []
    params      = []
    idx         = 1

    if filters.merchant_id:
        where_parts.append(f"t.merchant_id = ${idx}"); params.append(filters.merchant_id); idx += 1
    if filters.status:
        where_parts.append(f"t.status = ${idx}");      params.append(filters.status);      idx += 1
    if filters.from_date:
        where_parts.append(f"t.created_at >= ${idx}"); params.append(filters.from_date);   idx += 1
    if filters.to_date:
        where_parts.append(f"t.created_at <= ${idx}"); params.append(filters.to_date);     idx += 1

    where  = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
    order  = f"t.{filters.sort_by} {filters.sort_order.upper()}"
    offset = (filters.page - 1) * filters.page_size

    query = f"""
        {queries.LIST_TRANSACTIONS_BASE}
        {where}
        ORDER BY {order}
        LIMIT ${idx} OFFSET ${idx + 1}
    """
    params += [filters.page_size, offset]
    return query, params


@router.get("/transactions")
async def list_transactions(filters: TransactionFilters = Depends()):
    query, params = _build_list_query(filters)

    async with db.acquire() as conn:
        rows = await conn.fetch(query, *params)

    total = int(rows[0]["total_count"]) if rows else 0
    data  = [{k: v for k, v in dict(row).items() if k != "total_count"} for row in rows]

    return {
        "data": data,
        "pagination": {
            "page":        filters.page,
            "page_size":   filters.page_size,
            "total":       total,
            "total_pages": -(-total // filters.page_size),
        },
    }


@router.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    async with db.acquire() as conn:
        txn = await conn.fetchrow(queries.GET_TRANSACTION_BY_ID, transaction_id)
        if not txn:
            raise HTTPException(status_code=404, detail="Transaction not found")

        events = await conn.fetch(queries.GET_EVENTS_BY_TRANSACTION, transaction_id)

    return {
        **dict(txn),
        "events": [dict(e) for e in events],
    }