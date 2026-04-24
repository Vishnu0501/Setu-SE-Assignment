from fastapi import APIRouter, UploadFile, File, HTTPException
import json
from datetime import datetime
from app.database import db
from app.models.event import EventType, EVENT_TO_STATUS
from app.models.admin import SeedResponse
from app import queries

router = APIRouter(prefix="/admin")


@router.post("/seed", response_model=SeedResponse)
async def seed_from_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files accepted")

    try:
        events = json.loads(await file.read())
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    if not isinstance(events, list):
        raise HTTPException(status_code=400, detail="JSON must be a list of events")

    events.sort(key=lambda e: e["timestamp"])

    inserted = 0
    skipped  = 0

    async with db.acquire() as conn:
        for event in events:
            status    = EVENT_TO_STATUS[EventType(event["event_type"])].value
            timestamp = datetime.fromisoformat(event["timestamp"])

            await conn.execute(
                queries.UPSERT_MERCHANT_SEED,
                event["merchant_id"], event["merchant_name"],
            )
            await conn.execute(
                queries.UPSERT_TRANSACTION_SEED,
                event["transaction_id"], event["merchant_id"],
                event["amount"], event["currency"], status,
                timestamp, timestamp,
            )

            result = await conn.execute(
                queries.INSERT_EVENT_SEED,
                event["event_id"], event["event_type"],
                event["transaction_id"], event["merchant_id"],
                event["amount"], event["currency"], timestamp,
            )

            if result == "INSERT 0 1":
                inserted += 1
            else:
                skipped += 1

    return {
        "status":   "complete",
        "inserted": inserted,
        "skipped":  skipped,
        "total":    len(events),
    }