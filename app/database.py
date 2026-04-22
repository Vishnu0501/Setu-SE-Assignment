import os
import psycopg2
from psycopg2 import pool, OperationalError
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(
            1, 10,
            dsn=os.environ["DATABASE_URL"],
        )
    return _pool


def _reset_pool():
    global _pool
    try:
        if _pool:
            _pool.closeall()
    except Exception:
        pass
    _pool = None


@contextmanager
def get_db():
    global _pool
    p = get_pool()
    conn = p.getconn()
    conn.cursor_factory = RealDictCursor

    # Ping to detect stale connection (happens when Neon suspends after inactivity)
    # If stale, reset the entire pool and get a fresh connection
    try:
        conn.cursor().execute("SELECT 1")
    except OperationalError:
        try:
            p.putconn(conn, close=True)
        except Exception:
            pass
        _reset_pool()
        p = get_pool()
        conn = p.getconn()
        conn.cursor_factory = RealDictCursor

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            get_pool().putconn(conn)
        except Exception:
            pass


def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql")
    with open(schema_path) as f:
        schema = f.read()
    with get_db() as conn:
        conn.cursor().execute(schema)