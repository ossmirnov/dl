from game.board import BOARD_SIZE, HOME_BLUE, HOME_RED
from game.engine import GameState
from game.rng import Rng
from game.types import Cell, CellType, Color, PlayerState, Position


def empty_grid() -> list[list[Cell]]:
    return [[Cell(type=CellType.EMPTY) for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def make_state(
    *,
    cells: dict[Position, CellType] | None = None,
    open_cells: set[Position] | None = None,
    red_pos: Position = HOME_RED,
    blue_pos: Position = HOME_BLUE,
    seed: int = 1,
) -> GameState:
    grid = empty_grid()
    grid[HOME_RED[0]][HOME_RED[1]] = Cell(type=CellType.HOME_RED, is_open=True)
    grid[HOME_BLUE[0]][HOME_BLUE[1]] = Cell(type=CellType.HOME_BLUE, is_open=True)
    if cells:
        for pos, t in cells.items():
            grid[pos[0]][pos[1]] = Cell(type=t)
    if open_cells:
        for pos in open_cells:
            grid[pos[0]][pos[1]].is_open = True
    players = {
        Color.RED: PlayerState(color=Color.RED, home=HOME_RED, pos=red_pos),
        Color.BLUE: PlayerState(color=Color.BLUE, home=HOME_BLUE, pos=blue_pos),
    }
    return GameState(grid=grid, players=players, seed=seed, rng=Rng(seed=seed))
