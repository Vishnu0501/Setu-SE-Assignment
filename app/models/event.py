from enum import Enum
from pydantic import BaseModel, UUID4
from datetime import datetime


class EventType(str, Enum):
    payment_initiated = "payment_initiated"
    payment_processed = "payment_processed"
    payment_failed    = "payment_failed"
    settled           = "settled"


class TransactionStatus(str, Enum):
    initiated = "initiated"
    processed = "processed"
    failed    = "failed"
    settled   = "settled"


EVENT_TO_STATUS: dict[EventType, TransactionStatus] = {
    EventType.payment_initiated: TransactionStatus.initiated,
    EventType.payment_processed: TransactionStatus.processed,
    EventType.payment_failed:    TransactionStatus.failed,
    EventType.settled:           TransactionStatus.settled,
}


class EventIn(BaseModel):
    event_id:       UUID4
    event_type:     EventType
    transaction_id: UUID4
    merchant_id:    str
    merchant_name:  str
    amount:         float
    currency:       str
    timestamp:      datetime