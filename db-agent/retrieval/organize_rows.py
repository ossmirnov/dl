import json
from collections.abc import Mapping, Sequence, Set
from typing import cast

type Row = dict[str, object]
type Result = Row | list['Result']


def _to_hashable(v: object) -> object:
    try:
        hash(v)
        return v
    except TypeError:
        return json.dumps(v, sort_keys=True)


def clean_rows(rows: Sequence[Mapping[str, object]]) -> list[Row]:
    return [
        {
            key: val
            for key, val in row.items()
            if not key.startswith('_') and val is not None and val != ''
        }
        for row in rows
    ]


def _compress(rows: list[Row]) -> Result:
    if len(rows) == 0:
        return list[Result](rows)
    if len(rows) == 1:
        return rows[0]

    all_keys = set().union(*(r.keys() for r in rows))
    common: Row = {}
    varying: list[str] = []
    for key in all_keys:
        values = [r[key] for r in rows if key in r]
        if len(values) == len(rows) and len({_to_hashable(v) for v in values}) == 1:
            common[key] = values[0]
        else:
            varying.append(key)

    if common:
        remaining = [{k: v for k, v in r.items() if k not in common} for r in rows]
        remaining = [r for r in remaining if r]
        if not remaining:
            return common
        if len(remaining) == 1:
            return {**common, **remaining[0]}
        return {**common, 'items': _compress(remaining)}

    if not varying:
        return list[Result](rows)

    best_key = min(
        varying,
        key=lambda k: (any(k not in r for r in rows), len({_to_hashable(r.get(k)) for r in rows})),
    )
    groups: dict[object, list[Row]] = {}
    for row in rows:
        groups.setdefault(_to_hashable(row.get(best_key)), []).append(row)
    if len(groups) >= len(rows):
        return list[Result](rows)
    result: list[Result] = [_compress(group) for group in groups.values()]
    return result


def _separate(records: list[Row], sep_keys: Set[str]) -> Row:
    separated: Row = {}
    for key in sep_keys:
        seen: set[object] = set()
        values = []
        for r in records:
            if key not in r:
                continue
            h = _to_hashable(r[key])
            if h not in seen:
                seen.add(h)
                values.append(r[key])
        if not values:
            continue
        separated[key] = values[0] if len(values) == 1 else values
    remaining = [{k: v for k, v in r.items() if k not in sep_keys} for r in records]
    remaining = [r for r in remaining if r]
    if not remaining:
        return separated
    compressed = _compress(remaining)
    if isinstance(compressed, dict):
        return {**compressed, **separated}
    return {'items': compressed, **separated}


def _remove_prefix(rows: Sequence[Mapping[str, object]], prefix: str) -> list[Row]:
    return [{str(key).removeprefix(prefix): val for key, val in row.items()} for row in rows]


def organize_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    separate_cols: Set[str] = frozenset(),
    organize_cols: Set[str] = frozenset(),
    prefix: str = '',
) -> Result:
    if not isinstance(rows, list):
        raise ValueError(f'expected list of dicts, got {type(rows).__name__}')
    if not all(isinstance(r, dict) for r in rows):
        raise ValueError('expected list of dicts, got list containing non-dict')
    if not rows:
        return []
    if prefix:
        rows = _remove_prefix(rows, prefix)
    cleaned = clean_rows(rows)
    if not cleaned:
        return []
    if organize_cols:
        cleaned = [
            {
                k: organize_rows(cast(list[dict], v)) if k in organize_cols else v
                for k, v in row.items()
            }
            for row in cleaned
        ]
    matched = separate_cols & set().union(*(r.keys() for r in cleaned))
    if matched:
        return _separate(cleaned, matched)
    return _compress(cleaned)
