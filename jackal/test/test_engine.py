import pytest

from game.board import HOME_BLUE, HOME_RED
from game.engine import WIN_BALANCE, apply_move, new_game
from game.types import Ability, CellType, Color, Direction

from .helpers import make_state


def test_turn_alternation_basic():
    state = new_game(seed=1)
    assert state.turn == Color.RED


def test_stone_bounce():
    stone = (HOME_RED[0] + 1, HOME_RED[1])
    state = make_state(cells={stone: CellType.STONE})
    apply_move(state, color=Color.RED, direction=Direction.DOWN)
    assert state.players[Color.RED].pos == HOME_RED
    assert state.grid[stone[0]][stone[1]].is_open
    assert state.turn == Color.BLUE


def test_double_jumps_over_stone():
    stone = (HOME_RED[0] + 1, HOME_RED[1])
    landing = (HOME_RED[0] + 2, HOME_RED[1])
    state = make_state(cells={stone: CellType.STONE})
    state.players[Color.RED].abilities.add(Ability.DOUBLE)
    apply_move(state, color=Color.RED, direction=Direction.DOWN)
    assert state.players[Color.RED].pos == landing
    assert not state.grid[stone[0]][stone[1]].is_open


def test_double_bounces_off_landing_stone():
    landing = (HOME_RED[0] + 2, HOME_RED[1])
    state = make_state(cells={landing: CellType.STONE})
    state.players[Color.RED].abilities.add(Ability.DOUBLE)
    apply_move(state, color=Color.RED, direction=Direction.DOWN)
    assert state.players[Color.RED].pos == HOME_RED
    assert state.grid[landing[0]][landing[1]].is_open
    assert state.turn == Color.BLUE


def test_fly_to_any_non_stone():
    state = make_state()
    state.players[Color.RED].abilities.add(Ability.FLY)
    apply_move(state, color=Color.RED, fly_to=(4, 4))
    assert state.players[Color.RED].pos == (4, 4)


def test_fly_rejects_stone():
    state = make_state(cells={(4, 4): CellType.STONE})
    state.players[Color.RED].abilities.add(Ability.FLY)
    with pytest.raises(ValueError):
        apply_move(state, color=Color.RED, fly_to=(4, 4))


def test_fly_requires_ability():
    state = make_state()
    with pytest.raises(ValueError):
        apply_move(state, color=Color.RED, fly_to=(4, 4))


def test_swamp_skips_one_turn():
    swamp = (HOME_RED[0] + 1, HOME_RED[1])
    state = make_state(cells={swamp: CellType.SWAMP})
    apply_move(state, color=Color.RED, direction=Direction.DOWN)
    assert state.turn == Color.BLUE
    apply_move(state, color=Color.BLUE, direction=Direction.UP)
    assert state.turn == Color.BLUE


def test_double_persists_until_normalize():
    pos1 = (HOME_RED[0] + 1, HOME_RED[1])
    state = make_state(cells={pos1: CellType.DOUBLE, (3, 9): CellType.NORMALIZE})
    apply_move(state, color=Color.RED, direction=Direction.DOWN)
    assert Ability.DOUBLE in state.players[Color.RED].abilities
    state.turn = Color.RED
    apply_move(state, color=Color.RED, direction=Direction.DOWN)
    assert state.players[Color.RED].pos == (3, 9)
    assert Ability.DOUBLE not in state.players[Color.RED].abilities


def test_double_cleared_on_home():
    state = make_state(red_pos=(2, 9))
    state.players[Color.RED].abilities.add(Ability.DOUBLE)
    apply_move(state, color=Color.RED, direction=Direction.UP)
    assert state.players[Color.RED].pos == HOME_RED
    assert state.players[Color.RED].abilities == set()


def test_tunnel_returns_home_clears_abilities():
    state = make_state(cells={(5, 5): CellType.TUNNEL}, red_pos=(5, 4))
    state.players[Color.RED].abilities.add(Ability.FLY)
    apply_move(state, color=Color.RED, direction=Direction.RIGHT)
    assert state.players[Color.RED].pos == HOME_RED
    assert state.players[Color.RED].abilities == set()


def test_win_at_threshold():
    state = make_state(red_pos=(5, 5))
    state.players[Color.RED].balance = WIN_BALANCE - 1
    state.grid[5][6].type = CellType.MONEY
    apply_move(state, color=Color.RED, direction=Direction.RIGHT)
    assert state.winner == Color.RED


def test_no_moves_after_win():
    state = make_state()
    state.winner = Color.RED
    with pytest.raises(ValueError):
        apply_move(state, color=Color.RED, direction=Direction.DOWN)


def test_wizard_cascades_one_level():
    wizard = (5, 5)
    state = make_state(
        cells={
            wizard: CellType.WIZARD,
            (4, 5): CellType.MONEY,
            (5, 4): CellType.WIZARD,
            (5, 6): CellType.THIEF,
            (6, 5): CellType.EMPTY,
        },
        red_pos=(5, 4),
    )
    state.players[Color.BLUE].balance = 60
    state.grid[5][4].is_open = True
    apply_move(state, color=Color.RED, direction=Direction.RIGHT)
    assert state.grid[4][5].is_open
    assert state.grid[5][6].is_open
    assert state.grid[6][5].is_open
    assert state.grid[5][4].is_open
    assert state.players[Color.RED].balance >= 20
    assert state.players[Color.BLUE].balance == 40


def test_off_board_rejected():
    state = make_state(red_pos=(0, 9))
    with pytest.raises(ValueError):
        apply_move(state, color=Color.RED, direction=Direction.UP)


def test_wizard_refires_on_revisit():
    wizard_pos = (5, 5)
    state = make_state(
        cells={
            wizard_pos: CellType.WIZARD,
            (4, 5): CellType.MONEY,
            (5, 4): CellType.MONEY,
            (5, 6): CellType.MONEY,
            (6, 5): CellType.MONEY,
        },
        red_pos=(4, 5),
        open_cells={wizard_pos, (4, 5)},
    )
    apply_move(state, color=Color.RED, direction=Direction.DOWN)
    assert state.players[Color.RED].pos == wizard_pos
    assert state.grid[6][5].is_open
    assert state.grid[5][4].is_open
    assert state.grid[5][6].is_open


def test_wrong_turn_rejected():
    state = make_state()
    with pytest.raises(ValueError):
        apply_move(state, color=Color.BLUE, direction=Direction.UP)
