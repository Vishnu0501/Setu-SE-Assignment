import os

from contextlib import contextmanager

import psycopg2
from psycopg2 import pool

from psycopg2.extras import RealDictCursor

from dotenv import load_dotenv

load_dotenv()

_pool = None

def get_pool():
    global _pool

    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(1, 10,dsn = os.environ.get("DATABASE_URL"))
    return _pool

@contextmanager
def get_db():
    conn = get_pool().getconn()
    conn.cursor_factory = RealDictCursor
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        get_pool().putconn(conn)

def init_db():
    schema_path = os.path.join(os.path.dirname(__file__),"..","db","schema.sql")
    with open(schema_path) as f:
        schema = f.read()
    with get_db() as conn:
        conn.cursor().execute(schema)