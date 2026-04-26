import pytest

from game.distribution import DEFAULT_DISTRIBUTION, total, validate
from game.types import CellType


def test_default_total_plus_homes_equals_100():
    assert total(DEFAULT_DISTRIBUTION) + 2 == 100


def test_validate_rejects_wrong_total():
    bad = dict(DEFAULT_DISTRIBUTION)
    bad[CellType.EMPTY] += 1
    with pytest.raises(ValueError):
        validate(bad, board_cells=100)


def test_validate_rejects_home_in_distribution():
    bad = dict(DEFAULT_DISTRIBUTION)
    bad[CellType.HOME_RED] = 1
    with pytest.raises(ValueError):
        validate(bad, board_cells=100)


def test_validate_passes_default():
    validate(DEFAULT_DISTRIBUTION, board_cells=100)
