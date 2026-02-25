from agents import TResponseInputItem
from agents.memory import SessionSettings
from sqlalchemy import BigInteger, Column, MetaData, String, Table, delete, func, insert, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.schema import DDL

POSTGRES_DSN = 'postgresql+asyncpg://postgres@localhost:5432/postgres'
HISTORY_DSN = 'postgresql+asyncpg://postgres@localhost:5432/db_agent_history'

_metadata = MetaData()

_pg_database = Table('pg_database', MetaData(), Column('datname', String))

_session_items = Table(
    'session_items',
    _metadata,
    Column('id', BigInteger, primary_key=True),
    Column('session_id', String, nullable=False),
    Column('item', JSONB, nullable=False),
)

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(HISTORY_DSN, pool_size=5, max_overflow=0)
    return _engine


async def ensure_db() -> None:
    bootstrap = create_async_engine(POSTGRES_DSN, isolation_level='AUTOCOMMIT')
    async with bootstrap.connect() as conn:
        exists = await conn.scalar(
            select(_pg_database.c.datname).where(_pg_database.c.datname == 'db_agent_history')
        )
        if not exists:
            await conn.execute(DDL('CREATE DATABASE db_agent_history'))
    await bootstrap.dispose()

    async with get_engine().begin() as conn:
        await conn.run_sync(_metadata.create_all)


class PostgresSession:
    session_settings: SessionSettings | None = None

    def __init__(self, session_id: str):
        self.session_id = session_id

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]:
        q = (
            select(_session_items.c.item)
            .where(_session_items.c.session_id == self.session_id)
            .order_by(_session_items.c.id)
        )
        if limit is not None:
            q = q.limit(limit)
        async with get_engine().connect() as conn:
            rows = (await conn.execute(q)).fetchall()
        return [row.item for row in rows]

    async def add_items(self, items: list[TResponseInputItem]) -> None:
        async with get_engine().begin() as conn:
            await conn.execute(
                insert(_session_items),
                [{'session_id': self.session_id, 'item': item} for item in items],
            )

    async def pop_item(self) -> TResponseInputItem | None:
        stmt = (
            delete(_session_items)
            .where(
                _session_items.c.id
                == select(func.max(_session_items.c.id))
                .where(_session_items.c.session_id == self.session_id)
                .scalar_subquery()
            )
            .returning(_session_items.c.item)
        )
        async with get_engine().begin() as conn:
            row = (await conn.execute(stmt)).fetchone()
        return row.item if row else None

    async def clear_session(self) -> None:
        async with get_engine().begin() as conn:
            await conn.execute(
                delete(_session_items).where(_session_items.c.session_id == self.session_id)
            )
