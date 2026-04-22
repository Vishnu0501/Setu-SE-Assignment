import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()


class Database:
    _instance = None
    _pool     = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                dsn=os.environ["DATABASE_URL"],
                min_size=1,
                max_size=10,
                command_timeout=60,
            )

    async def disconnect(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def init_schema(self):
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "db", "schema.sql"
        )
        with open(schema_path) as f:
            schema = f.read()
        async with self._pool.acquire() as conn:
            await conn.execute(schema)

    def acquire(self):
        """Return a connection context manager from the pool."""
        return self._pool.acquire()


db = Database()