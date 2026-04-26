from collections import Counter

from game.board import (
    BOARD_SIZE,
    HOME_BLUE,
    HOME_RED,
    generate,
    is_connected_non_stone,
    neighbors,
)
from game.distribution import DEFAULT_DISTRIBUTION
from game.rng import Rng
from game.types import CellType


def _flat_types(grid: list) -> list[CellType]:
    return [c.type for row in grid for c in row]


def test_generate_has_correct_homes():
    grid = generate(rng=Rng(seed=1))
    assert grid[HOME_RED[0]][HOME_RED[1]].type == CellType.HOME_RED
    assert grid[HOME_BLUE[0]][HOME_BLUE[1]].type == CellType.HOME_BLUE
    assert grid[HOME_RED[0]][HOME_RED[1]].is_open
    assert grid[HOME_BLUE[0]][HOME_BLUE[1]].is_open


def test_generate_distribution_matches():
    grid = generate(rng=Rng(seed=42))
    counts = Counter(_flat_types(grid))
    assert counts[CellType.HOME_RED] == 1
    assert counts[CellType.HOME_BLUE] == 1
    for t, n in DEFAULT_DISTRIBUTION.items():
        assert counts[t] == n, (t, counts[t], n)


def test_non_stone_cells_connected():
    for seed in range(20):
        grid = generate(rng=Rng(seed=seed))
        assert is_connected_non_stone(grid)


def test_home_neighbors_never_stone():
    for seed in range(20):
        grid = generate(rng=Rng(seed=seed))
        for h in (HOME_RED, HOME_BLUE):
            for n in neighbors(h):
                assert grid[n[0]][n[1]].type != CellType.STONE


def test_seed_reproducibility():
    g1 = generate(rng=Rng(seed=7))
    g2 = generate(rng=Rng(seed=7))
    assert _flat_types(g1) == _flat_types(g2)


def test_neighbors_corner():
    assert sorted(neighbors((0, 0))) == [(0, 1), (1, 0)]
    n = neighbors((0, BOARD_SIZE - 1))
    assert (0, BOARD_SIZE - 2) in n and (1, BOARD_SIZE - 1) in n
