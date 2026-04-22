from typing import Optional,List
from datetime import datetime
from pydantic import BaseModel
from fastapi import Query

class EventOut(BaseModel):
    event_id : str
    event_type : str
    amount : float
    currency : str
    timestamp : datetime
    received_at : datetime

class TransactionOut(BaseModel):
    transaction_id : str
    merchant_id : str
    merchant_name : str
    amount : float
    currency : str
    status : str
    created_at : datetime
    updated_at : datetime


class TransactionDetailOut(TransactionOut):
    events : List[EventOut]

class TransactionFilters:
    def __init__(
        self,
        merchant_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        sort_by:     str                = Query("created_at", enum=["created_at", "updated_at", "amount"]),
        sort_order:  str                = Query("desc", enum=["asc", "desc"]),
    ):
        self.merchant_id = merchant_id
        self.status      = status
        self.from_date   = from_date
        self.to_date     = to_date
        self.page        = page
        self.page_size   = page_size
        self.sort_by     = sort_by
        self.sort_order  = sort_order