#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Annotated, Optional

import typer
import yaml
from sqlalchemy import Column, ColumnElement, Engine, Table, or_, select

from db_util import DEFAULT_DB_CONFIG, DSN, DatabaseConfig, reflect_db
from organize_rows import organize_rows


def _norm(s: str) -> str:
    return ' '.join(w.capitalize() for w in s.strip().split()).replace('ё', 'е').replace('Ё', 'Е')


def _name_conditions(col: Column, last: str, first: str, pat: str | None) -> ColumnElement[bool]:
    if pat:
        return col.like(f'{last} {first} {pat}%')
    return or_(
        col.like(f'{last} {first}%'),
        col.like(f'{first} {last}%'),
    )


def _query_table(
    engine: Engine,
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
    with engine.connect() as conn:
        raw = [dict(row) for row in conn.execute(stmt).mappings()]
    if not raw:
        return None, None
    raw.sort(key=lambda r: -len(str(r.get('name', ''))))
    prefix = f'{table.name}_'
    sep_keys = {col.removeprefix(prefix) for col in cfg.separate_cols}
    org_keys = {col.removeprefix(prefix) for col in cfg.organize_cols}
    return str(table.name), organize_rows(
        raw, separate_cols=sep_keys, organize_cols=org_keys, prefix=prefix
    )


def filter_by_name(
    last_name: str,
    first_name: str,
    patronymic: str | None = None,
    *,
    dsn: str = DSN,
    db_config: DatabaseConfig | None = None,
) -> dict[str, object]:
    cfg = db_config or DEFAULT_DB_CONFIG
    last = _norm(last_name)
    first = _norm(first_name)
    pat = _norm(patronymic) if patronymic else None
    engine, metadata = reflect_db(dsn)
    tables = [t for t in metadata.sorted_tables if 'name' in t.columns]
    results: dict[str, object] = {}
    with ThreadPoolExecutor(max_workers=len(tables) or 1) as executor:
        futures = {
            executor.submit(_query_table, engine, t, last, first, pat, cfg): t for t in tables
        }
        for future in as_completed(futures):
            name, data = future.result()
            if name is not None:
                results[name] = data
    return dict(sorted(results.items()))


def filter_by_name_and_print(
    last_name: str,
    first_name: str,
    patronymic: Annotated[Optional[str], typer.Argument()] = None,
    dsn: str = DSN,
    db_config: Annotated[
        DatabaseConfig | None, typer.Option(parser=DatabaseConfig.model_validate_json)
    ] = None,
) -> None:
    results = filter_by_name(last_name, first_name, patronymic, dsn=dsn, db_config=db_config)
    print(yaml.dump(results, allow_unicode=True, default_flow_style=False, sort_keys=False))


if __name__ == '__main__':
    typer.run(filter_by_name_and_print)
