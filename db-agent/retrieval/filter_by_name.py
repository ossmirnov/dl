#!/usr/bin/env python3
import asyncio
from typing import Annotated, Optional

import typer
import yaml
from sqlalchemy import Column, ColumnElement, MetaData, Table, or_, select
from sqlalchemy.ext.asyncio import AsyncEngine

from retrieval.db_util import DATA_DSN, DEFAULT_DB_CONFIG, DatabaseConfig, async_reflect_db
from retrieval.organize_rows import organize_rows


def _norm(s: str) -> str:
    return ' '.join(w.capitalize() for w in s.strip().split()).replace('ё', 'е').replace('Ё', 'Е')


def _name_conditions(col: Column, last: str, first: str, pat: str | None) -> ColumnElement[bool]:
    if pat:
        return col.like(f'{last} {first} {pat}%')
    return or_(
        col.like(f'{last} {first}%'),
        col.like(f'{first} {last}%'),
    )


async def _query_table(
    engine: AsyncEngine,
    table: Table,
    last: str,
    first: str,
    pat: str | None,
    cfg: DatabaseConfig,
) -> tuple[str | None, object | None]:
    if 'name' not in table.columns:
        return None, None
    cols = [c for c in table.columns if c.name not in cfg.ignore_cols]
    stmt = select(*cols).where(_name_conditions(table.c.name, last, first, pat))
    async with engine.connect() as conn:
        raw = [dict(row) for row in (await conn.execute(stmt)).mappings()]
    if not raw:
        return None, None
    raw.sort(key=lambda r: -len(str(r.get('name', ''))))
    prefix = f'{table.name}_'
    sep_keys = {col.removeprefix(prefix) for col in cfg.separate_cols}
    org_keys = {col.removeprefix(prefix) for col in cfg.organize_cols}
    return str(table.name), organize_rows(
        raw, separate_cols=sep_keys, organize_cols=org_keys, prefix=prefix
    )


async def filter_by_name(
    last_name: str,
    first_name: str,
    patronymic: str | None = None,
    *,
    dsn: str = DATA_DSN,
    engine: AsyncEngine | None = None,
    metadata: MetaData | None = None,
    db_config: DatabaseConfig | None = None,
) -> dict[str, object]:
    cfg = db_config or DEFAULT_DB_CONFIG
    last = _norm(last_name)
    first = _norm(first_name)
    pat = _norm(patronymic) if patronymic else None
    if engine is None or metadata is None:
        _engine, _metadata = await async_reflect_db(dsn)
        own_engine = True
    else:
        _engine, _metadata, own_engine = engine, metadata, False
    tables = [t for t in _metadata.sorted_tables if 'name' in t.columns]
    results_list = await asyncio.gather(
        *[_query_table(_engine, t, last, first, pat, cfg) for t in tables]
    )
    if own_engine:
        await _engine.dispose()
    return dict(sorted((n, d) for n, d in results_list if n is not None))


def filter_by_name_and_print(
    last_name: str,
    first_name: str,
    patronymic: Annotated[Optional[str], typer.Argument()] = None,
    dsn: str = DATA_DSN,
    db_config: Annotated[
        DatabaseConfig | None, typer.Option(parser=DatabaseConfig.model_validate_json)
    ] = None,
) -> None:
    results = asyncio.run(
        filter_by_name(last_name, first_name, patronymic, dsn=dsn, db_config=db_config)
    )
    print(yaml.dump(results, allow_unicode=True, default_flow_style=False, sort_keys=False))


if __name__ == '__main__':
    typer.run(filter_by_name_and_print)
