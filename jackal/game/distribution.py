from .types import CellType


DEFAULT_DISTRIBUTION: dict[CellType, int] = {
    CellType.STONE: 10,
    CellType.MONEY: 30,
    CellType.SWAP: 4,
    CellType.TUNNEL: 5,
    CellType.DOUBLE: 5,
    CellType.FLY: 3,
    CellType.SWAMP: 5,
    CellType.TELEPORT: 4,
    CellType.THIEF: 4,
    CellType.WIZARD: 4,
    CellType.NORMALIZE: 4,
    CellType.EMPTY: 20,
}


def total(distribution: dict[CellType, int]) -> int:
    return sum(distribution.values())


def validate(distribution: dict[CellType, int], *, board_cells: int) -> None:
    s = total(distribution)
    if s + 2 != board_cells:
        raise ValueError(f'distribution sums to {s}, expected {board_cells - 2}')
    for forbidden in (CellType.HOME_RED, CellType.HOME_BLUE):
        if forbidden in distribution:
            raise ValueError(f'distribution must not include {forbidden.value}')
