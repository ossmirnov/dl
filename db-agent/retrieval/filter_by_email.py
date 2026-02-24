#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Annotated
import typer
import yaml
from sqlalchemy import Engine, Table, select

from db_util import DEFAULT_DB_CONFIG, DSN, DatabaseConfig, reflect_db
from organize_rows import organize_rows


def _query_table(
    engine: Engine,
    table: Table,
    email: str,
    cfg: DatabaseConfig,
) -> tuple[str | None, object | None]:
    cols = [c for c in table.columns if c.name not in cfg.ignore_cols]
    stmt = select(*cols).where(table.c.email == email)
    with engine.connect() as conn:
        raw = [dict(row) for row in conn.execute(stmt).mappings()]
    if not raw:
        return None, None
    prefix = f'{table.name}_'
    sep_keys = {col.removeprefix(prefix) for col in cfg.separate_cols}
    org_keys = {col.removeprefix(prefix) for col in cfg.organize_cols}
    return str(table.name), organize_rows(
        raw, separate_cols=sep_keys, organize_cols=org_keys, prefix=prefix
    )


def filter_by_email(
    email: str,
    *,
    dsn: str = DSN,
    db_config: DatabaseConfig | None = None,
) -> dict[str, object]:
    cfg = db_config or DEFAULT_DB_CONFIG
    email = email.lower()
    engine, metadata = reflect_db(dsn)
    tables = [t for t in metadata.sorted_tables if 'email' in t.columns]
    results: dict[str, object] = {}
    with ThreadPoolExecutor(max_workers=len(tables) or 1) as executor:
        futures = {executor.submit(_query_table, engine, t, email, cfg): t for t in tables}
        for future in as_completed(futures):
            name, data = future.result()
            if name is not None:
                results[name] = data
    return dict(sorted(results.items()))


def filter_by_email_and_print(
    email: str,
    dsn: str = DSN,
    db_config: Annotated[
        DatabaseConfig | None, typer.Option(parser=DatabaseConfig.model_validate_json)
    ] = None,
) -> None:
    results = filter_by_email(email, dsn=dsn, db_config=db_config)
    print(yaml.dump(results, allow_unicode=True, default_flow_style=False, sort_keys=False))


if __name__ == '__main__':
    typer.run(filter_by_email_and_print)
