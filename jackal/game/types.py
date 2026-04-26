from dataclasses import dataclass, field
from enum import Enum


class CellType(str, Enum):
    HOME_RED = 'home_red'
    HOME_BLUE = 'home_blue'
    EMPTY = 'empty'
    MONEY = 'money'
    SWAP = 'swap'
    TUNNEL = 'tunnel'
    DOUBLE = 'double'
    FLY = 'fly'
    SWAMP = 'swamp'
    TELEPORT = 'teleport'
    STONE = 'stone'
    THIEF = 'thief'
    WIZARD = 'wizard'
    NORMALIZE = 'normalize'


class Color(str, Enum):
    RED = 'red'
    BLUE = 'blue'


class Direction(str, Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'


class Ability(str, Enum):
    DOUBLE = 'double'
    FLY = 'fly'


Position = tuple[int, int]


@dataclass
class Cell:
    type: CellType
    is_open: bool = False
    revealed_value: int = 0


@dataclass
class PlayerState:
    color: Color
    home: Position
    pos: Position
    balance: int = 0
    abilities: set[Ability] = field(default_factory=set)
    skip_next_turn: bool = False


_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.UP: (-1, 0),
    Direction.DOWN: (1, 0),
    Direction.LEFT: (0, -1),
    Direction.RIGHT: (0, 1),
}


def opponent(c: Color) -> Color:
    return Color.BLUE if c == Color.RED else Color.RED


def direction_delta(d: Direction) -> tuple[int, int]:
    return _DELTAS[d]


def home_type(c: Color) -> CellType:
    return CellType.HOME_RED if c == Color.RED else CellType.HOME_BLUE
