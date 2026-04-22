from fastapi import APIRouter, Depends
from app.models.reconciliation import SummaryFilters, DiscrepancyFilters
from app.database import db
from app import queries

router = APIRouter()


def _build_date_filter(filters) -> tuple[str, list]:
    """Returns (date_filter_sql_fragment, params_list)."""
    date_filter = ""
    params      = []
    idx         = 1

    if filters.from_date:
        date_filter += f" AND t.created_at >= ${idx}"
        params.append(filters.from_date)
        idx += 1
    if filters.to_date:
        date_filter += f" AND t.created_at <= ${idx}"
        params.append(filters.to_date)

    return date_filter, params


async def _fetch_discrepancy(conn, query: str) -> list:
    rows = await conn.fetch(query)
    return [dict(r) for r in rows]


@router.get("/reconciliation/summary")
async def reconciliation_summary(filters: SummaryFilters = Depends()):
    date_filter, params = _build_date_filter(filters)

    query_map = {
        "merchant": queries.SUMMARY_BY_MERCHANT,
        "date":     queries.SUMMARY_BY_DATE,
        "status":   queries.SUMMARY_BY_STATUS,
    }
    query = query_map[filters.group_by].format(date_filter=date_filter)

    async with db.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return {"group_by": filters.group_by, "data": [dict(r) for r in rows]}


@router.get("/reconciliation/discrepancies")
async def reconciliation_discrepancies(filters: DiscrepancyFilters = Depends()):
    results = {}

    async with db.acquire() as conn:
        if filters.type is None or filters.type == "processed_not_settled":
            results["processed_not_settled"] = await _fetch_discrepancy(
                conn, queries.DISCREPANCY_PROCESSED_NOT_SETTLED
            )
        if filters.type is None or filters.type == "settled_after_failure":
            results["settled_after_failure"] = await _fetch_discrepancy(
                conn, queries.DISCREPANCY_SETTLED_AFTER_FAILURE
            )
        if filters.type is None or filters.type == "conflicting_states":
            results["conflicting_states"] = await _fetch_discrepancy(
                conn, queries.DISCREPANCY_CONFLICTING_STATES
            )

    if filters.type:
        data = results.get(filters.type, [])
        return {"type": filters.type, "count": len(data), "data": data}

    return {
        "summary": {k: len(v) for k, v in results.items()},
        "data":    results,
    }