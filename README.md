# Setu Payment Service

A backend service for ingesting payment lifecycle events, tracking transaction state, and surfacing reconciliation discrepancies.

**Live URL:** https://setu-se-assignment-0x8o.onrender.com  
**API Docs:** https://setu-se-assignment-0x8o.onrender.com/docs

---

## Architecture

```
POST /events
    └── Idempotent ingestion → upsert merchants + transactions → insert event

GET /transactions            → filtered, paginated, sorted list
GET /transactions/{id}       → transaction detail + full event history

GET /reconciliation/summary        → GROUP BY merchant / date / status
GET /reconciliation/discrepancies  → detect inconsistent payment/settlement state

POST /admin/seed             → load sample_events.json via file upload
```


### Schema

| Table | Purpose |
|---|---|
| `merchants` | One row per merchant, upserted on first event |
| `transactions` | One row per transaction; status reflects latest event by timestamp |
| `events` | Immutable event log; `event_id` PRIMARY KEY enforces idempotency at DB level |

### Indexes

```sql
idx_transactions_merchant_id  -- fast merchant filtering
idx_transactions_status       -- fast status filtering
idx_transactions_created_at   -- fast date range filtering
idx_events_transaction_id     -- fast event history lookup
idx_events_event_type         -- fast discrepancy queries
idx_events_timestamp          -- fast timeline ordering
```

---

## Local Setup

### Prerequisites
- Python 3.12+
- Docker Desktop (for docker compose option)

### Option A — Docker Compose (recommended, one command)

```bash
git clone <your-repo-url>
cd setu-payment-service

docker compose up --build
```

App runs at `http://localhost:8000`. Then seed:

```bash
# Via API (Postman)
POST http://localhost:8000/admin/seed
Body → form-data → file → select sample_events.json
```

### Option B — Direct with Neon DB

```bash
git clone <your-repo-url>
cd setu-payment-service

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

cp .env.example .env
# Set DATABASE_URL in .env to your Neon connection string

uvicorn app.main:app --reload
```

Tables are created automatically on startup via `init_schema()`.

---

## API Reference

### `POST /events`
Ingest a payment lifecycle event. Idempotent on `event_id`.

**Supported event types:** `payment_initiated` · `payment_processed` · `payment_failed` · `settled`

**Request body:**
```json
{
  "event_id":       "550e8400-e29b-41d4-a716-446655440000",
  "event_type":     "payment_initiated",
  "transaction_id": "550e8400-e29b-41d4-a716-446655440001",
  "merchant_id":    "merchant_1",
  "merchant_name":  "AcmeCorp",
  "amount":         1500.00,
  "currency":       "INR",
  "timestamp":      "2026-01-08T12:00:00+00:00"
}
```

**Response:**
```json
{ "status": "accepted", "event_id": "..." }
// or on duplicate:
{ "status": "already_processed", "event_id": "..." }
```

---

### `GET /transactions`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `merchant_id` | string | — | Filter by merchant |
| `status` | string | — | `initiated` / `processed` / `failed` / `settled` |
| `from_date` | datetime | — | Range start (inclusive) |
| `to_date` | datetime | — | Range end (inclusive) |
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Max 100 |
| `sort_by` | string | `created_at` | `created_at` / `updated_at` / `amount` |
| `sort_order` | string | `desc` | `asc` / `desc` |

---

### `GET /transactions/{transaction_id}`
Returns transaction details, merchant info, and full event history sorted by timestamp.

---

### `GET /reconciliation/summary`

| Parameter | Values |
|---|---|
| `group_by` | `merchant` (default) / `date` / `status` |
| `from_date` | optional date filter |
| `to_date` | optional date filter |

---

### `GET /reconciliation/discrepancies`

| Parameter | Values |
|---|---|
| `type` | `processed_not_settled` / `settled_after_failure` / `conflicting_states` / omit for all |

Discrepancy types:
- **processed_not_settled** — `payment_processed` received but no `settled` event exists
- **settled_after_failure** — `settled` event exists alongside a `payment_failed` event
- **conflicting_states** — both `payment_processed` and `payment_failed` recorded for same transaction

---

### `POST /admin/seed`
Upload a JSON file to seed the database.

```
Body → form-data → Key: file, Type: File → upload sample_events.json
```

> ⚠️ For demo purposes only. In production this would be protected with API key authentication.

---

## Deployment

**Hosting:** [Render](https://render.com) (free tier Web Service)  
**Database:** [Neon](https://neon.tech) (serverless PostgreSQL, free tier)

### Deploy your own

1. Fork this repo and push to GitHub
2. Create a free PostgreSQL DB at [neon.tech](https://neon.tech) — copy connection string
3. On [render.com](https://render.com): **New → Web Service → connect repo**
   - Runtime: Docker
   - Environment variable: `DATABASE_URL = <neon-url>?sslmode=require`
4. Deploy — tables created automatically on first startup
5. Seed via `POST /admin/seed` from Postman

> **Note:** Render free tier spins down after 15 minutes of inactivity. First request after sleep may take ~30 seconds due to cold start.

---

## Assumptions & Tradeoffs

- **Status = latest timestamp wins.** When conflicting events arrive (e.g. both `payment_processed` and `payment_failed`), `transactions.status` reflects whichever had the later timestamp. Both events are preserved and surface as `conflicting_states` discrepancies.
- **No separate settlements table.** Settlement state is derived from `event_type = 'settled'` in the events table. Avoids duplication while supporting all reconciliation queries.
- **Idempotency at DB level.** `event_id PRIMARY KEY` guarantees duplicate inserts fail with a constraint violation — caught and returned as `already_processed`. No application-level locking needed.
- **Pagination uses window function.** `COUNT(*) OVER()` returns total count alongside paginated rows in one query — no extra round-trip.
- **Sync routes with asyncpg.** All routes are `async def` with asyncpg for true async DB access.
- **Schema via `IF NOT EXISTS`.** Tables created on startup using `CREATE TABLE IF NOT EXISTS` — safe to run on every deploy. For a production system with evolving schema, Alembic migrations would be used instead.
- **No auth on `/admin/seed`.** Intentional for demo purposes. In production, this would require API key or admin token.
- **Base image CVEs.** `python:3.12-slim` may contain low-severity OS-level CVEs inherited from Debian. In production, this would be addressed by pinning to a specific digest and running automated image scanning (Trivy/Snyk) in CI.
- **Testing approach.** Integration testing done via Postman collection (included in repo). Unit tests with `pytest-asyncio` would be the next step with more time.

---

## AI Disclosure

ChatGPT was used during this assignment — primarily for quick syntax lookups and clarifying Python/asyncpg documentation.