from dataclasses import dataclass, field
from typing import Any

from .board import BOARD_SIZE, HOME_BLUE, HOME_RED, generate
from .cells import CASCADE_SKIP, EffectCtx, apply_effect
from .moves import can_double, can_fly, double_target, in_bounds, is_stone, step_target
from .rng import Rng
from .types import (
    Cell,
    CellType,
    Color,
    Direction,
    PlayerState,
    Position,
    home_type,
    opponent,
)


WIN_BALANCE = 100


@dataclass
class GameEvent:
    kind: str
    payload: dict[str, Any]


@dataclass
class GameState:
    grid: list[list[Cell]]
    players: dict[Color, PlayerState]
    turn: Color = Color.RED
    winner: Color | None = None
    turn_count: int = 0
    seed: int | None = None
    rng: Rng = field(default_factory=lambda: Rng())
    events: list[GameEvent] = field(default_factory=list)


def new_game(*, seed: int | None = None) -> GameState:
    rng = Rng(seed=seed)
    grid = generate(rng=rng)
    players = {
        Color.RED: PlayerState(color=Color.RED, home=HOME_RED, pos=HOME_RED),
        Color.BLUE: PlayerState(color=Color.BLUE, home=HOME_BLUE, pos=HOME_BLUE),
    }
    return GameState(grid=grid, players=players, seed=seed, rng=rng)


def _emit(state: GameState, kind: str, **payload: Any) -> None:
    state.events.append(GameEvent(kind=kind, payload=payload))


def _open_cell(state: GameState, pos: Position) -> bool:
    cell = state.grid[pos[0]][pos[1]]
    if cell.is_open:
        return False
    cell.is_open = True
    _emit(state, 'opened', pos=list(pos), cell_type=cell.type.value)
    return True


def _trigger_effect(state: GameState, *, actor: Color, cell_pos: Position) -> list[Position]:
    ctx = EffectCtx(
        grid=state.grid,
        players=state.players,
        rng=state.rng,
        actor=actor,
        cell_pos=cell_pos,
    )
    cell = state.grid[cell_pos[0]][cell_pos[1]]
    cascade = apply_effect(ctx)
    _emit(
        state,
        'effect',
        pos=list(cell_pos),
        cell_type=cell.type.value,
        actor=actor.value,
    )
    return cascade


def _wizard_cascade(state: GameState, *, actor: Color, targets: list[Position]) -> None:
    for tpos in targets:
        if not in_bounds(tpos):
            continue
        ncell = state.grid[tpos[0]][tpos[1]]
        _open_cell(state, tpos)
        if ncell.type in CASCADE_SKIP:
            continue
        _trigger_effect(state, actor=actor, cell_pos=tpos)
        _check_home_clears(state, actor)
        if state.players[actor].balance >= WIN_BALANCE:
            state.winner = actor
            return


def _check_home_clears(state: GameState, actor: Color) -> None:
    me = state.players[actor]
    if me.pos == me.home:
        if me.abilities:
            me.abilities.clear()
            _emit(state, 'abilities_cleared', actor=actor.value, reason='home')


def _check_win(state: GameState, actor: Color) -> None:
    if state.players[actor].balance >= WIN_BALANCE:
        state.winner = actor
        _emit(state, 'win', actor=actor.value)


def _advance_turn(state: GameState) -> None:
    state.turn_count += 1
    state.turn = opponent(state.turn)
    nxt = state.players[state.turn]
    while nxt.skip_next_turn and state.winner is None:
        nxt.skip_next_turn = False
        _emit(state, 'skipped', actor=state.turn.value)
        state.turn_count += 1
        state.turn = opponent(state.turn)
        nxt = state.players[state.turn]


def apply_move(
    state: GameState,
    *,
    color: Color,
    direction: Direction | None = None,
    fly_to: Position | None = None,
) -> None:
    if state.winner is not None:
        raise ValueError('game has ended')
    if state.turn != color:
        raise ValueError('not your turn')
    me = state.players[color]

    if fly_to is not None:
        if not can_fly(me):
            raise ValueError('cannot fly without fly ability')
        if direction is not None:
            raise ValueError('cannot specify both direction and fly_to')
        if not in_bounds(fly_to):
            raise ValueError('fly target out of bounds')
        if is_stone(state.grid, fly_to):
            raise ValueError('cannot fly onto stone')
        if fly_to == me.pos:
            raise ValueError('fly target must differ from current position')
        me.pos = fly_to
        _emit(state, 'flew', actor=color.value, pos=list(fly_to))
        _activate_landing(state, color)
        _check_home_clears(state, color)
        _check_win(state, color)
        if state.winner is None:
            _advance_turn(state)
        return

    if direction is None:
        raise ValueError('direction or fly_to required')

    if can_double(me):
        target = double_target(player=me, direction=direction)
        used_double = True
    else:
        target = step_target(player=me, direction=direction)
        used_double = False

    if not in_bounds(target):
        raise ValueError('move out of bounds')

    if is_stone(state.grid, target):
        _open_cell(state, target)
        _emit(state, 'bounced', actor=color.value, pos=list(target), used_double=used_double)
        _advance_turn(state)
        return

    me.pos = target
    _emit(state, 'moved', actor=color.value, pos=list(target), used_double=used_double)
    _activate_landing(state, color)
    _check_home_clears(state, color)
    _check_win(state, color)
    if state.winner is None:
        _advance_turn(state)


def _activate_landing(state: GameState, actor: Color) -> None:
    _activate_one(state, actor, allow_recurse=True)


def _activate_one(state: GameState, actor: Color, *, allow_recurse: bool) -> None:
    me = state.players[actor]
    pos_before = me.pos
    cell = state.grid[me.pos[0]][me.pos[1]]
    opened = _open_cell(state, me.pos)
    if opened:
        cascade = _trigger_effect(state, actor=actor, cell_pos=me.pos)
        if cell.type == CellType.WIZARD:
            _wizard_cascade(state, actor=actor, targets=cascade)
    elif cell.type == CellType.TUNNEL:
        _trigger_effect(state, actor=actor, cell_pos=me.pos)
    elif cell.type == CellType.WIZARD:
        cascade = _trigger_effect(state, actor=actor, cell_pos=me.pos)
        _wizard_cascade(state, actor=actor, targets=cascade)

    if not allow_recurse:
        return
    if me.pos == pos_before:
        return
    if state.grid[me.pos[0]][me.pos[1]].is_open:
        return
    _activate_one(state, actor, allow_recurse=False)


