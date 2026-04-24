from pydantic import BaseModel


class SeedResponse(BaseModel):
    status:   str
    inserted: int
    skipped:  int
    total:    int