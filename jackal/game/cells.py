from dataclasses import dataclass
from typing import Callable

from .board import neighbors
from .rng import Rng
from .types import Ability, Cell, CellType, Color, PlayerState, Position, opponent


@dataclass
class EffectCtx:
    grid: list[list[Cell]]
    players: dict[Color, PlayerState]
    rng: Rng
    actor: Color
    cell_pos: Position


def _cell(ctx: EffectCtx) -> Cell:
    r, c = ctx.cell_pos
    return ctx.grid[r][c]


def _no_effect(_: EffectCtx) -> list[Position]:
    return []


def _money(ctx: EffectCtx) -> list[Position]:
    cell = _cell(ctx)
    if cell.revealed_value == 0:
        cell.revealed_value = ctx.rng.randint(1, 10)
    ctx.players[ctx.actor].balance += cell.revealed_value
    return []


def _swap(ctx: EffectCtx) -> list[Position]:
    me = ctx.players[ctx.actor]
    other = ctx.players[opponent(ctx.actor)]
    me.pos, other.pos = other.pos, me.pos
    return []


def _tunnel(ctx: EffectCtx) -> list[Position]:
    me = ctx.players[ctx.actor]
    me.pos = me.home
    return []


def _double(ctx: EffectCtx) -> list[Position]:
    ctx.players[ctx.actor].abilities.add(Ability.DOUBLE)
    return []


def _fly(ctx: EffectCtx) -> list[Position]:
    ctx.players[ctx.actor].abilities.add(Ability.FLY)
    return []


def _swamp(ctx: EffectCtx) -> list[Position]:
    ctx.players[ctx.actor].skip_next_turn = True
    return []


def _teleport(ctx: EffectCtx) -> list[Position]:
    me = ctx.players[ctx.actor]
    other = ctx.players[opponent(ctx.actor)]
    candidates: list[Position] = []
    for n in neighbors(other.pos):
        if ctx.grid[n[0]][n[1]].type == CellType.STONE:
            continue
        if n == me.pos:
            continue
        candidates.append(n)
    if candidates:
        me.pos = ctx.rng.choice(candidates)
    else:
        me.pos = other.pos
    return []


def _thief(ctx: EffectCtx) -> list[Position]:
    me = ctx.players[ctx.actor]
    other = ctx.players[opponent(ctx.actor)]
    amount = other.balance // 3
    if amount > 0:
        other.balance -= amount
        me.balance += amount
    return []


def _wizard(ctx: EffectCtx) -> list[Position]:
    return neighbors(ctx.cell_pos)


def _normalize(ctx: EffectCtx) -> list[Position]:
    ctx.players[ctx.actor].abilities.clear()
    return []


EFFECTS: dict[CellType, Callable[[EffectCtx], list[Position]]] = {
    CellType.HOME_RED: _no_effect,
    CellType.HOME_BLUE: _no_effect,
    CellType.EMPTY: _no_effect,
    CellType.STONE: _no_effect,
    CellType.MONEY: _money,
    CellType.SWAP: _swap,
    CellType.TUNNEL: _tunnel,
    CellType.DOUBLE: _double,
    CellType.FLY: _fly,
    CellType.SWAMP: _swamp,
    CellType.TELEPORT: _teleport,
    CellType.THIEF: _thief,
    CellType.WIZARD: _wizard,
    CellType.NORMALIZE: _normalize,
}


CASCADE_SKIP: set[CellType] = {
    CellType.WIZARD,
    CellType.STONE,
    CellType.HOME_RED,
    CellType.HOME_BLUE,
    CellType.EMPTY,
}


def apply_effect(ctx: EffectCtx) -> list[Position]:
    cell = _cell(ctx)
    return EFFECTS[cell.type](ctx)
