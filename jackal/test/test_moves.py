from game.board import BOARD_SIZE
from game.moves import (
    can_double,
    can_fly,
    double_target,
    in_bounds,
    is_stone,
    step_target,
)
from game.types import Ability, Cell, CellType, Direction, PlayerState, Color

from .helpers import empty_grid


def _player(pos):
    return PlayerState(color=Color.RED, home=(0, 0), pos=pos)


def test_in_bounds():
    assert in_bounds((0, 0))
    assert in_bounds((BOARD_SIZE - 1, BOARD_SIZE - 1))
    assert not in_bounds((-1, 0))
    assert not in_bounds((0, BOARD_SIZE))


def test_step_target():
    p = _player((5, 5))
    assert step_target(player=p, direction=Direction.UP) == (4, 5)
    assert step_target(player=p, direction=Direction.DOWN) == (6, 5)
    assert step_target(player=p, direction=Direction.LEFT) == (5, 4)
    assert step_target(player=p, direction=Direction.RIGHT) == (5, 6)


def test_double_target():
    p = _player((5, 5))
    assert double_target(player=p, direction=Direction.UP) == (3, 5)
    assert double_target(player=p, direction=Direction.RIGHT) == (5, 7)


def test_can_double_and_fly():
    p = _player((0, 0))
    assert not can_double(p)
    assert not can_fly(p)
    p.abilities.add(Ability.DOUBLE)
    assert can_double(p)
    p.abilities.add(Ability.FLY)
    assert can_fly(p)


def test_is_stone():
    grid = empty_grid()
    grid[3][4] = Cell(type=CellType.STONE)
    assert is_stone(grid, (3, 4))
    assert not is_stone(grid, (3, 5))
