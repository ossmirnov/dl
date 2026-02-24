from pathlib import Path

from pydantic import BaseModel, Field
from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

DSN = 'postgresql://readonly@localhost/db_agent_data'
ASYNC_DSN = 'postgresql+asyncpg://readonly@localhost/db_agent_data'

DB_CONFIG_PATH = Path(__file__).parent / '../data/db_config.json'


class DatabaseConfig(BaseModel):
    ignore_cols: set[str] = Field(default_factory=set)
    separate_cols: set[str] = Field(default_factory=set)
    organize_cols: set[str] = Field(default_factory=set)


try:
    DEFAULT_DB_CONFIG = DatabaseConfig.model_validate_json(DB_CONFIG_PATH.read_text())
except FileNotFoundError:
    DEFAULT_DB_CONFIG = DatabaseConfig()


def parse_columns(s: str | list) -> list[str]:
    return s.split(',') if isinstance(s, str) else s


def reflect_db(dsn: str):
    engine = create_engine(dsn, pool_size=20, max_overflow=0)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    return engine, metadata


async def async_reflect_db(dsn: str = ASYNC_DSN) -> tuple[AsyncEngine, MetaData]:
    engine = create_async_engine(dsn, pool_size=20, max_overflow=0)
    metadata = MetaData()
    async with engine.connect() as conn:
        await conn.run_sync(metadata.reflect)
    return engine, metadata
