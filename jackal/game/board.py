from collections import deque

from .distribution import DEFAULT_DISTRIBUTION, validate
from .rng import Rng
from .types import Cell, CellType, Position


BOARD_SIZE = 10
HOME_RED: Position = (0, BOARD_SIZE - 1)
HOME_BLUE: Position = (BOARD_SIZE - 1, 0)


def neighbors(pos: Position, *, size: int = BOARD_SIZE) -> list[Position]:
    r, c = pos
    out: list[Position] = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < size and 0 <= nc < size:
            out.append((nr, nc))
    return out


def _is_connected_without(stones: set[Position], *, size: int, start: Position) -> bool:
    target = size * size - len(stones)
    seen: set[Position] = {start}
    q: deque[Position] = deque([start])
    while q:
        p = q.popleft()
        for n in neighbors(p, size=size):
            if n in stones or n in seen:
                continue
            seen.add(n)
            q.append(n)
    return len(seen) == target


def _stone_forbidden() -> set[Position]:
    f = {HOME_RED, HOME_BLUE}
    f.update(neighbors(HOME_RED, size=BOARD_SIZE))
    f.update(neighbors(HOME_BLUE, size=BOARD_SIZE))
    return f


def _place_stones(*, count: int, rng: Rng) -> set[Position]:
    forbidden = _stone_forbidden()
    cells = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if (r, c) not in forbidden]
    rng.shuffle(cells)
    stones: set[Position] = set()
    for p in cells:
        if len(stones) == count:
            break
        candidate = stones | {p}
        if _is_connected_without(candidate, size=BOARD_SIZE, start=HOME_RED):
            stones.add(p)
    if len(stones) != count:
        raise RuntimeError(f'could not place {count} stones with connectivity')
    return stones


def generate(*, rng: Rng, distribution: dict[CellType, int] | None = None) -> list[list[Cell]]:
    dist = dict(distribution) if distribution is not None else dict(DEFAULT_DISTRIBUTION)
    validate(dist, board_cells=BOARD_SIZE * BOARD_SIZE)

    stones = _place_stones(count=dist[CellType.STONE], rng=rng)

    grid: list[list[Cell]] = [
        [Cell(type=CellType.EMPTY) for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)
    ]
    grid[HOME_RED[0]][HOME_RED[1]] = Cell(type=CellType.HOME_RED, is_open=True)
    grid[HOME_BLUE[0]][HOME_BLUE[1]] = Cell(type=CellType.HOME_BLUE, is_open=True)
    for s in stones:
        grid[s[0]][s[1]] = Cell(type=CellType.STONE)

    pool: list[CellType] = []
    for t, n in dist.items():
        if t == CellType.STONE:
            continue
        pool.extend([t] * n)
    rng.shuffle(pool)

    free_cells = [
        (r, c)
        for r in range(BOARD_SIZE)
        for c in range(BOARD_SIZE)
        if (r, c) not in {HOME_RED, HOME_BLUE} and (r, c) not in stones
    ]
    if len(pool) != len(free_cells):
        raise RuntimeError(f'pool {len(pool)} != free {len(free_cells)}')
    for pos, t in zip(free_cells, pool):
        grid[pos[0]][pos[1]] = Cell(type=t)
    return grid


def is_connected_non_stone(grid: list[list[Cell]]) -> bool:
    size = len(grid)
    stones = {(r, c) for r in range(size) for c in range(size) if grid[r][c].type == CellType.STONE}
    return _is_connected_without(stones, size=size, start=HOME_RED)
