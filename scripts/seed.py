import json
import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv()

EVENT_STATUS_MAP = {
    "payment_initiated": "initiated",
    "payment_processed": "processed",
    "payment_failed":    "failed",
    "settled":           "settled",
}


def seed(filepath: str = "sample_events.json"):
    with open(filepath) as f:
        events = json.load(f)

    events.sort(key=lambda e: e["timestamp"])

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur  = conn.cursor()

    print(f"Seeding {len(events)} events...")

    for i, event in enumerate(events):
        status = EVENT_STATUS_MAP.get(event["event_type"], "initiated")

        cur.execute(
            """
            INSERT INTO merchants (merchant_id, merchant_name)
            VALUES (%s, %s)
            ON CONFLICT (merchant_id) DO NOTHING
            """,
            (event["merchant_id"], event["merchant_name"]),
        )

        cur.execute(
            """
            INSERT INTO transactions
                (transaction_id, merchant_id, amount, currency, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (transaction_id) DO UPDATE SET
                status     = CASE
                                 WHEN transactions.updated_at < EXCLUDED.updated_at
                                 THEN EXCLUDED.status
                                 ELSE transactions.status
                             END,
                updated_at = GREATEST(transactions.updated_at, EXCLUDED.updated_at)
            """,
            (
                event["transaction_id"], event["merchant_id"],
                event["amount"],         event["currency"],
                status,                  event["timestamp"],
                event["timestamp"],
            ),
        )

        cur.execute(
            """
            INSERT INTO events
                (event_id, event_type, transaction_id, merchant_id, amount, currency, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO NOTHING
            """,
            (
                event["event_id"],       event["event_type"],
                event["transaction_id"], event["merchant_id"],
                event["amount"],         event["currency"],
                event["timestamp"],
            ),
        )

        if (i + 1) % 1000 == 0:
            conn.commit()
            print(f"  {i + 1} events inserted...")

    conn.commit()
    cur.close()
    conn.close()
    print("Done. Seeding complete!")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "sample_events.json"
    seed(path)