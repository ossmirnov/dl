from .board import BOARD_SIZE
from .types import Ability, Cell, CellType, Direction, PlayerState, Position, direction_delta


def in_bounds(pos: Position, *, size: int = BOARD_SIZE) -> bool:
    r, c = pos
    return 0 <= r < size and 0 <= c < size


def is_stone(grid: list[list[Cell]], pos: Position) -> bool:
    return grid[pos[0]][pos[1]].type == CellType.STONE


def step_target(*, player: PlayerState, direction: Direction) -> Position:
    dr, dc = direction_delta(direction)
    r, c = player.pos
    return (r + dr, c + dc)


def double_target(*, player: PlayerState, direction: Direction) -> Position:
    dr, dc = direction_delta(direction)
    r, c = player.pos
    return (r + 2 * dr, c + 2 * dc)


def can_double(player: PlayerState) -> bool:
    return Ability.DOUBLE in player.abilities


def can_fly(player: PlayerState) -> bool:
    return Ability.FLY in player.abilities
