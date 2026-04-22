from pydantic import BaseModel,UUID4
from datetime import datetime

class EventIn(BaseModel):
    event_id: UUID4
    event_type: str
    transaction_id: UUID4
    merchant_id: str
    merchant_name: str
    amount: float
    currency: str
    timestamp: datetime