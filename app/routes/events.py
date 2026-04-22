from fastapi import APIRouter, HTTPException
from app.models.event import EventIn, EVENT_TO_STATUS
from app.database import db
from app import queries

router = APIRouter()


@router.post("/events", status_code=200)
async def ingest_event(event: EventIn):
    status = EVENT_TO_STATUS[event.event_type].value

    async with db.acquire() as conn:
        async with conn.transaction():

            existing = await conn.fetchrow(
                queries.CHECK_EVENT_EXISTS, str(event.event_id)
            )
            if existing:
                return {"status": "already_processed", "event_id": str(event.event_id)}

            await conn.execute(
                queries.UPSERT_MERCHANT,
                event.merchant_id, event.merchant_name,
            )

            await conn.execute(
                queries.UPSERT_TRANSACTION,
                str(event.transaction_id), event.merchant_id,
                event.amount, event.currency, status,
                event.timestamp, event.timestamp,
            )

            await conn.execute(
                queries.INSERT_EVENT,
                str(event.event_id), event.event_type.value,
                str(event.transaction_id), event.merchant_id,
                event.amount, event.currency, event.timestamp,
            )

    return {"status": "accepted", "event_id": str(event.event_id)}