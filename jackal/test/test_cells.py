from game.board import HOME_BLUE, HOME_RED
from game.cells import EffectCtx, apply_effect
from game.types import Ability, CellType, Color

from .helpers import make_state


def _ctx_at(state, *, actor: Color, pos):
    return EffectCtx(
        grid=state.grid,
        players=state.players,
        rng=state.rng,
        actor=actor,
        cell_pos=pos,
    )


def test_money_rolls_in_range_and_persists():
    pos = (5, 5)
    state = make_state(cells={pos: CellType.MONEY}, red_pos=pos)
    apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
    cell = state.grid[pos[0]][pos[1]]
    assert 1 <= cell.revealed_value <= 10
    assert state.players[Color.RED].balance == cell.revealed_value
    apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
    assert state.players[Color.RED].balance == 2 * cell.revealed_value


def test_swap_exchanges_positions():
    pos = (2, 3)
    state = make_state(cells={pos: CellType.SWAP}, red_pos=pos, blue_pos=(7, 4))
    apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
    assert state.players[Color.RED].pos == (7, 4)
    assert state.players[Color.BLUE].pos == pos


def test_tunnel_sends_actor_home():
    pos = (4, 4)
    state = make_state(cells={pos: CellType.TUNNEL}, red_pos=pos)
    apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
    assert state.players[Color.RED].pos == HOME_RED


def test_double_grants_ability():
    pos = (3, 3)
    state = make_state(cells={pos: CellType.DOUBLE}, red_pos=pos)
    apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
    assert Ability.DOUBLE in state.players[Color.RED].abilities


def test_fly_grants_ability():
    pos = (3, 3)
    state = make_state(cells={pos: CellType.FLY}, red_pos=pos)
    apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
    assert Ability.FLY in state.players[Color.RED].abilities


def test_swamp_sets_skip():
    pos = (3, 3)
    state = make_state(cells={pos: CellType.SWAMP}, red_pos=pos)
    apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
    assert state.players[Color.RED].skip_next_turn


def test_teleport_lands_adjacent_to_opponent():
    pos = (2, 2)
    state = make_state(cells={pos: CellType.TELEPORT}, red_pos=pos, blue_pos=(5, 5))
    apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
    new_pos = state.players[Color.RED].pos
    dr = abs(new_pos[0] - 5)
    dc = abs(new_pos[1] - 5)
    assert dr + dc == 1


def test_teleport_avoids_stones():
    pos = (2, 2)
    state = make_state(
        cells={
            pos: CellType.TELEPORT,
            (4, 5): CellType.STONE,
            (5, 4): CellType.STONE,
            (5, 6): CellType.STONE,
        },
        red_pos=pos,
        blue_pos=(5, 5),
    )
    for _ in range(20):
        state.players[Color.RED].pos = pos
        apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
        assert state.players[Color.RED].pos == (6, 5)


def test_thief_takes_third_rounded_down():
    pos = (2, 2)
    state = make_state(cells={pos: CellType.THIEF}, red_pos=pos)
    state.players[Color.BLUE].balance = 50
    apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
    assert state.players[Color.RED].balance == 16
    assert state.players[Color.BLUE].balance == 34


def test_thief_rounds_down_small():
    pos = (2, 2)
    state = make_state(cells={pos: CellType.THIEF}, red_pos=pos)
    state.players[Color.BLUE].balance = 2
    apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
    assert state.players[Color.RED].balance == 0
    assert state.players[Color.BLUE].balance == 2


def test_thief_floors_at_zero():
    pos = (2, 2)
    state = make_state(cells={pos: CellType.THIEF}, red_pos=pos)
    apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
    assert state.players[Color.RED].balance == 0
    assert state.players[Color.BLUE].balance == 0


def test_wizard_returns_neighbours():
    pos = (4, 4)
    state = make_state(cells={pos: CellType.WIZARD}, red_pos=pos)
    targets = apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
    assert set(targets) == {(3, 4), (5, 4), (4, 3), (4, 5)}


def test_normalize_clears_abilities():
    pos = (3, 3)
    state = make_state(cells={pos: CellType.NORMALIZE}, red_pos=pos)
    state.players[Color.RED].abilities = {Ability.DOUBLE, Ability.FLY}
    apply_effect(_ctx_at(state, actor=Color.RED, pos=pos))
    assert state.players[Color.RED].abilities == set()
