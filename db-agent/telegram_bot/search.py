import json

import yaml
from retrieval.db_util import ASYNC_DSN, DEFAULT_DB_CONFIG, async_reflect_db
from retrieval.filter_by_address import filter_by_address as _filter_by_address
from retrieval.filter_by_email import filter_by_email as _filter_by_email
from retrieval.filter_by_name import filter_by_name as _filter_by_name
from retrieval.filter_by_phone import filter_by_phone as _filter_by_phone
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncEngine

_engine: AsyncEngine | None = None
_metadata: MetaData | None = None


async def init_retrieval() -> None:
    global _engine, _metadata
    _engine, _metadata = await async_reflect_db(ASYNC_DSN)


def _db() -> tuple[AsyncEngine, MetaData]:
    if _engine is None or _metadata is None:
        raise RuntimeError('Retrieval DB not initialized')
    return _engine, _metadata


def to_yaml(data: object) -> str:
    return yaml.dump(
        json.loads(json.dumps(data, ensure_ascii=False, default=str)),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )


async def search_phone(phone: int) -> dict:
    engine, metadata = _db()
    return await _filter_by_phone(phone, engine=engine, metadata=metadata, db_config=DEFAULT_DB_CONFIG)


async def search_email(email: str) -> dict:
    engine, metadata = _db()
    return await _filter_by_email(email, engine=engine, metadata=metadata, db_config=DEFAULT_DB_CONFIG)


async def search_name(last: str, first: str, patronymic: str) -> dict:
    engine, metadata = _db()
    return await _filter_by_name(
        last, first, patronymic, engine=engine, metadata=metadata, db_config=DEFAULT_DB_CONFIG
    )


async def search_address(city: str, street: str, house: str, apartment: str | None) -> list:
    engine, metadata = _db()
    return await _filter_by_address(
        city, street, house, apartment, engine=engine, metadata=metadata, db_config=DEFAULT_DB_CONFIG
    )
