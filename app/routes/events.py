from fastapi import HTTPException,APIRouter
from app.models.event import EventIn
from app.database import get_db

router = APIRouter()

EVENT_STATUS_MAP = {
    "payment_initiated": "initiated",
    "payment_processed": "processed",
    "payment_failed":    "failed",
    "settled":           "settled",
}

@router.post("/events",status_code=200)
def ingest_event(event: EventIn):
    status = EVENT_STATUS_MAP.get(event.event_type)
    if not status:
        raise HTTPException(status_code=422, detail=f"Unknown event_type: {event.event_type}")
    
    with get_db() as conn:
        # Idempotency check
        cur = conn.cursor()
        cur.execute(
            "SELECT event_id FROM events WHERE event_id = %s",(str(event.event_id),)
        )
        if cur.fetchone():
            return {"status": "already_processed", "event_id": str(event.event_id)}
        
        cur.execute(
            """
            INSERT INTO merchants (merchant_id, merchant_name)
            VALUES (%s, %s)
            ON CONFLICT (merchant_id) DO UPDATE SET merchant_name = EXCLUDED.merchant_name
            """,
            (event.merchant_id, event.merchant_name),
        )
         # Upsert transaction — only advance status if the incoming event is newer
        cur.execute(
            """
            INSERT INTO transactions
            (transaction_id, merchant_id, amount, currency, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (transaction_id) DO UPDATE SET
            status = CASE
                WHEN transactions.updated_at < EXCLUDED.updated_at
                THEN EXCLUDED.status
                ELSE transactions.status
                
            END,
            updated_at = GREATEST(transactions.updated_at, EXCLUDED.updated_at)
            """,
            (
                str(event.transaction_id),
                event.merchant_id,
                event.amount,
                event.currency,
                status,
                event.timestamp,
                event.timestamp,
            ),
        )
        # Insert event record
        cur.execute(
            """
            INSERT INTO events (event_id, event_type, transaction_id, merchant_id, amount, currency, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(event.event_id),
                event.event_type,
                str(event.transaction_id),
                event.merchant_id,
                event.amount,
                event.currency,
                event.timestamp,
            ),
        )

    return {"status": "accepted", "event_id": str(event.event_id)}