#!/usr/bin/env python3
import asyncio
from typing import Annotated

import typer
import yaml
from sqlalchemy import MetaData, Table, select
from sqlalchemy.ext.asyncio import AsyncEngine

from retrieval.db_util import DATA_DSN, DEFAULT_DB_CONFIG, DatabaseConfig, async_reflect_db
from retrieval.organize_rows import organize_rows


async def _query_table(
    engine: AsyncEngine,
    table: Table,
    email: str,
    cfg: DatabaseConfig,
) -> tuple[str | None, object | None]:
    cols = [c for c in table.columns if c.name not in cfg.ignore_cols]
    stmt = select(*cols).where(table.c.email == email)
    async with engine.connect() as conn:
        raw = [dict(row) for row in (await conn.execute(stmt)).mappings()]
    if not raw:
        return None, None
    prefix = f'{table.name}_'
    sep_keys = {col.removeprefix(prefix) for col in cfg.separate_cols}
    org_keys = {col.removeprefix(prefix) for col in cfg.organize_cols}
    return str(table.name), organize_rows(
        raw, separate_cols=sep_keys, organize_cols=org_keys, prefix=prefix
    )


async def filter_by_email(
    email: str,
    *,
    dsn: str = DATA_DSN,
    engine: AsyncEngine | None = None,
    metadata: MetaData | None = None,
    db_config: DatabaseConfig | None = None,
) -> dict[str, object]:
    cfg = db_config or DEFAULT_DB_CONFIG
    email = email.lower()
    if engine is None or metadata is None:
        _engine, _metadata = await async_reflect_db(dsn)
        own_engine = True
    else:
        _engine, _metadata, own_engine = engine, metadata, False
    tables = [t for t in _metadata.sorted_tables if 'email' in t.columns]
    results_list = await asyncio.gather(*[_query_table(_engine, t, email, cfg) for t in tables])
    if own_engine:
        await _engine.dispose()
    return dict(sorted((n, d) for n, d in results_list if n is not None))


def filter_by_email_and_print(
    email: str,
    dsn: str = DATA_DSN,
    db_config: Annotated[
        DatabaseConfig | None, typer.Option(parser=DatabaseConfig.model_validate_json)
    ] = None,
) -> None:
    results = asyncio.run(filter_by_email(email, dsn=dsn, db_config=db_config))
    print(yaml.dump(results, allow_unicode=True, default_flow_style=False, sort_keys=False))


if __name__ == '__main__':
    typer.run(filter_by_email_and_print)
