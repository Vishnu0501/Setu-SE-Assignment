from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import db
from app.response import AppJSONResponse
from app.routes import events, transactions, reconciliation


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    await db.init_schema()
    yield
    await db.disconnect()


app = FastAPI(
    title="Setu Payment Service",
    description="Payment lifecycle event ingestion and reconciliation service",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=AppJSONResponse,
)

app.include_router(events.router,         tags=["Events"])
app.include_router(transactions.router,   tags=["Transactions"])
app.include_router(reconciliation.router, tags=["Reconciliation"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}