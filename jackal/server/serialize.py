from typing import Any

from game.board import BOARD_SIZE
from game.engine import GameEvent, GameState
from game.types import Cell, CellType, Color


def _cell_to_dict(cell: Cell) -> dict[str, Any]:
    if not cell.is_open:
        return {'type': 'closed'}
    out: dict[str, Any] = {'type': cell.type.value}
    if cell.type == CellType.MONEY and cell.revealed_value > 0:
        out['value'] = cell.revealed_value
    return out


def state_to_dict(state: GameState) -> dict[str, Any]:
    return {
        'board_size': BOARD_SIZE,
        'cells': [[_cell_to_dict(c) for c in row] for row in state.grid],
        'players': {
            color.value: {
                'pos': list(p.pos),
                'home': list(p.home),
                'balance': p.balance,
                'abilities': sorted(a.value for a in p.abilities),
                'skip_next_turn': p.skip_next_turn,
            }
            for color, p in state.players.items()
        },
        'turn': state.turn.value,
        'winner': state.winner.value if state.winner is not None else None,
        'turn_count': state.turn_count,
    }


def events_to_list(events: list[GameEvent]) -> list[dict[str, Any]]:
    return [{'kind': e.kind, **e.payload} for e in events]
