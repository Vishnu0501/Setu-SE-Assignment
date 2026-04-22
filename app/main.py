from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from app.routes import events, transactions, reconciliation
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()   # runs schema.sql on startup — creates tables if they don't exist
    yield
app = FastAPI(
    title="Setu Payment Service",
    description="Payment lifecycle event ingestion and reconciliation service",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(events.router,         tags=["Events"])
app.include_router(transactions.router,   tags=["Transactions"])
app.include_router(reconciliation.router, tags=["Reconciliation"])
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

