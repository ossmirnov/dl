#!/usr/bin/env python3
from contextlib import asynccontextmanager
from typing import Any

import json
from mcp.server.fastmcp import Context, FastMCP

from db_util import ASYNC_DSN, DEFAULT_DB_CONFIG, async_reflect_db
from filter_by_address import filter_by_address as _filter_by_address
from filter_by_email import filter_by_email as _filter_by_email
from filter_by_name import filter_by_name as _filter_by_name
from filter_by_phone import filter_by_phone as _filter_by_phone


@asynccontextmanager
async def lifespan(_server: FastMCP):
    engine, metadata = await async_reflect_db(ASYNC_DSN)
    try:
        yield {'engine': engine, 'metadata': metadata}
    finally:
        await engine.dispose()


mcp = FastMCP('db-retrieval', lifespan=lifespan)


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


@mcp.tool(
    description=(
        'Search all tables by phone number. Returns structured data grouped by source table.'
    )
)
async def filter_by_phone(phone_number: int, ctx: Context) -> str:
    lc = ctx.request_context.lifespan_context
    results = await _filter_by_phone(
        phone_number, engine=lc['engine'], metadata=lc['metadata'], db_config=DEFAULT_DB_CONFIG
    )
    return _json(results)


@mcp.tool(
    description='Search all tables by email. Returns structured data grouped by source table.'
)
async def filter_by_email(email: str, ctx: Context) -> str:
    lc = ctx.request_context.lifespan_context
    results = await _filter_by_email(
        email, engine=lc['engine'], metadata=lc['metadata'], db_config=DEFAULT_DB_CONFIG
    )
    return _json(results)


@mcp.tool(
    description=(
        'Search by full name (last, first, optional patronymic). '
        'Best for rare names; avoid common names without patronymic.'
    )
)
async def filter_by_name(
    last_name: str, first_name: str, patronymic: str | None, ctx: Context
) -> str:
    lc = ctx.request_context.lifespan_context
    results = await _filter_by_name(
        last_name,
        first_name,
        patronymic,
        engine=lc['engine'],
        metadata=lc['metadata'],
        db_config=DEFAULT_DB_CONFIG,
    )
    return _json(results)


@mcp.tool(
    description=(
        'Fuzzy-search by address (city, street, house, optional apartment). '
        'Returns candidates ranked by match score.'
    )
)
async def filter_by_address(
    city: str, street: str, house: str, apartment: str | None, ctx: Context
) -> str:
    lc = ctx.request_context.lifespan_context
    results = await _filter_by_address(
        city,
        street,
        house,
        apartment,
        engine=lc['engine'],
        metadata=lc['metadata'],
        db_config=DEFAULT_DB_CONFIG,
    )
    return _json(results)


if __name__ == '__main__':
    mcp.run()
