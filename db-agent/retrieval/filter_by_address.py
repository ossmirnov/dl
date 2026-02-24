#!/usr/bin/env python3
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Annotated, Optional

import typer
import yaml
from sqlalchemy import Engine, Table, func, literal, select, text

from db_util import DEFAULT_DB_CONFIG, DSN, DatabaseConfig, reflect_db
from organize_rows import organize_rows

_city_prefix = re.compile(
    r'^(г\.?\s+|город\s+|пос\.?\s+|посёлок\s+|поселок\s+|п\.\s*|с\.\s+|село\s+|деревня\s+|дер\.\s+|рп\.\s+)',
    re.IGNORECASE,
)
_city_suffix = re.compile(r'\s+[гс]$', re.IGNORECASE)
_compound_types = re.compile(r'(?<!\w)(пр-кт|б-р|пр-зд)(?!\w)', re.IGNORECASE)
_street_types = re.compile(
    r'\b(улица|ул|проспект|пр|переулок|пер|бульвар|шоссе|ш|проезд|набережная|наб|тупик|площадь|пл|аллея|микрорайон|мкр|квартал|линия|дорога|дор)\b\.?',
    re.IGNORECASE,
)
_house_prefix = re.compile(r'^\s*(дом\s+|д\.\s*)', re.IGNORECASE)
_corpus_word = re.compile(r'\s*(корпус|корп\.?|кор\.?)\s*', re.IGNORECASE)
_building_word = re.compile(r'\s*(строение|стр\.?)\s*', re.IGNORECASE)
_apt_prefix = re.compile(r'^(кв\.?\s*|квартира\s*|офис\s*|оф\.?\s*|ком\.?\s*)', re.IGNORECASE)
_whitespace = re.compile(r'\s+')


def normalize_city(s: str | None) -> str | None:
    if not s:
        return None
    s = s.replace('ё', 'е').replace('Ё', 'Е')
    s = _city_prefix.sub('', s.strip().lower())
    s = _city_suffix.sub('', s).strip()
    return s.title() or None


def normalize_street(s: str | None) -> str | None:
    if not s:
        return None
    s = s.replace('ё', 'е').replace('Ё', 'Е')
    s = _compound_types.sub(' ', s.lower())
    s = _street_types.sub('', s)
    s = _whitespace.sub(' ', s).strip()
    return s.title() or None


def normalize_house(s: str | None) -> str | None:
    if not s:
        return None
    s = s.replace('ё', 'е').replace('Ё', 'Е')
    s = _house_prefix.sub('', s.lower().strip())
    s = _corpus_word.sub('к', s)
    s = _building_word.sub('с', s)
    return _whitespace.sub('', s).strip() or None


def normalize_apartment(s: str | None) -> str | None:
    if not s:
        return None
    s = s.replace('ё', 'е').replace('Ё', 'Е')
    s = _apt_prefix.sub('', str(s).lower().strip())
    return s.strip() or None


def _normalize_address_query(
    norm_city: str | None,
    norm_street: str | None,
    norm_house: str | None,
    norm_apt: str | None,
) -> str | None:
    tokens = [p.lower() for p in [norm_city, norm_street, norm_house, norm_apt] if p]
    return ' '.join(tokens) or None


def _query_table(
    engine: Engine,
    table: Table,
    norm_city: str,
    norm_street: str,
    norm_house: str,
    norm_apt: str | None,
    norm_query: str | None,
    cfg: DatabaseConfig,
) -> list[dict]:
    cols = {c.name for c in table.columns}
    if 'phone_number' not in cols:
        return []

    src = str(table.name)
    skip = cfg.ignore_cols | {'_sim', '_score_sql'}

    if 'address_norm' in cols and norm_query:
        sim = func.similarity(table.c.address_norm, literal(norm_query))
        stmt = select(*table.columns, sim.label('_sim')).where(
            table.c.address_norm.op('%')(literal(norm_query))
        )
        with engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [
            {
                **{str(k): v for k, v in row.items() if str(k) not in skip},
                '_score': round(float(row['_sim'] or 0), 4),
                '_source': src,
            }
            for row in rows
        ]

    if 'address_city' not in cols:
        return []

    missing = {'address_street', 'address_house', 'address_apartment'} - cols
    if missing:
        raise ValueError(f'{table.name}: address_city present but missing {missing}')

    street_sim = func.similarity(table.c.address_street, literal(norm_street))
    if norm_apt is not None:
        score = literal(0.6) + street_sim * 0.4
        stmt = (
            select(*table.columns, score.label('_score_sql'))
            .where(table.c.address_city == norm_city)
            .where(table.c.address_house == norm_house)
            .where(table.c.address_apartment == norm_apt)
            .where(table.c.address_street.op('%')(literal(norm_street)))
        )
    else:
        score = literal(0.5) + street_sim * 0.5
        stmt = (
            select(*table.columns, score.label('_score_sql'))
            .where(table.c.address_city == norm_city)
            .where(table.c.address_house == norm_house)
            .where(table.c.address_street.op('%')(literal(norm_street)))
        )
    with engine.connect() as conn:
        conn.execute(text('SET LOCAL pg_trgm.similarity_threshold = 0.45'))
        rows = conn.execute(stmt).mappings().all()
    return [
        {
            **{str(k): v for k, v in row.items() if str(k) not in skip},
            '_score': round(float(row['_score_sql'] or 0), 4),
            '_source': src,
        }
        for row in rows
    ]


def filter_by_address(
    city: str,
    street: str,
    house: str,
    apartment: str | None = None,
    *,
    dsn: str = DSN,
    limit: int | None = 5,
    tolerance: float = 1e-4,
    db_config: DatabaseConfig | None = None,
) -> list[dict]:
    cfg = db_config or DEFAULT_DB_CONFIG
    norm_city = normalize_city(city)
    norm_street = normalize_street(street)
    norm_house = normalize_house(house)
    norm_apt = normalize_apartment(apartment) if apartment else None
    norm_query = _normalize_address_query(norm_city, norm_street, norm_house, norm_apt)

    if not norm_city or not norm_street or not norm_house:
        return []

    engine, metadata = reflect_db(dsn)
    tables = [
        t
        for t in metadata.sorted_tables
        if {'address_city', 'address_norm'} & {c.name for c in t.columns}
    ]

    all_rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(tables) or 1) as executor:
        futures = {
            executor.submit(
                _query_table,
                engine,
                t,
                norm_city,
                norm_street,
                norm_house,
                norm_apt,
                norm_query,
                cfg,
            ): t
            for t in tables
        }
        for future in as_completed(futures):
            all_rows.extend(future.result())

    by_phone: dict[int, list[dict]] = defaultdict(list)
    for row in all_rows:
        by_phone[row['phone_number']].append(row)

    ranked = sorted(
        by_phone.items(),
        key=lambda kv: max(r['_score'] for r in kv[1]),
        reverse=True,
    )

    best_overall = ranked[0][1] if ranked else []
    threshold = max(r['_score'] for r in best_overall) - tolerance if best_overall else 0.0

    output = []
    for phone, rows in ranked[:limit]:
        best_score = max(r['_score'] for r in rows)
        if best_score < threshold:
            break
        by_source: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            by_source[row['_source']].append({k: v for k, v in row.items() if k != 'phone_number'})
        sources = {}
        for src, src_rows in sorted(by_source.items()):
            prefix = f'{src}_'
            sep_keys = {col.removeprefix(prefix) for col in cfg.separate_cols}
            org_keys = {col.removeprefix(prefix) for col in cfg.organize_cols}
            sources[src] = organize_rows(
                src_rows, separate_cols=sep_keys, organize_cols=org_keys, prefix=prefix
            )
        output.append({'score': round(best_score * 100), 'phone_number': phone, **sources})

    return output


def filter_by_address_and_print(
    city: str,
    street: str,
    house: str,
    apartment: Annotated[Optional[str], typer.Argument()] = None,
    dsn: str = DSN,
    limit: Annotated[Optional[int], typer.Option()] = 5,
    db_config: Annotated[
        DatabaseConfig | None, typer.Option(parser=DatabaseConfig.model_validate_json)
    ] = None,
    tolerance: Annotated[float, typer.Option()] = 1e-4,
) -> None:
    results = filter_by_address(
        city,
        street,
        house,
        apartment,
        dsn=dsn,
        limit=limit,
        tolerance=tolerance,
        db_config=db_config,
    )
    print(yaml.dump(results, allow_unicode=True, default_flow_style=False, sort_keys=False))


if __name__ == '__main__':
    typer.run(filter_by_address_and_print)
