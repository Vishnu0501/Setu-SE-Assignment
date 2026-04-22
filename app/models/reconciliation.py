from typing import Optional
from datetime import date
from fastapi import Query

class SummaryFilters:
    def __init__(
            self,
            group_by: str = Query("merchant", enum=["merchant", "date", "status"]),
            from_date: Optional[date] = None,
            to_date:   Optional[date] = None,
    ):
        self.group_by = group_by
        self.from_date = from_date
        self.to_date = to_date


class DiscrepancyFilters:
    def __init__(
            self,
            type: Optional[str] = Query(
                None,
                enum=["processed_not_settled", "settled_after_failure", "conflicting_states"],
            )
        ):
        self.type = type