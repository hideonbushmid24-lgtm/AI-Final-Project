
import pytest

from tank_battle.constants import (
    PlayerId,
    Direction,
)

from tank_battle.entities import (
    Position,
    Tank,
    Base,
    Wall,
)

from tank_battle.game_state import GameState
from tank_battle.scenario import create_default_scenario


def make_state():
    tanks = {
        PlayerId.PLAYER_1: Tank(
            PlayerId.PLAYER_1,
            Position(1, 5),
            Direction.UP
        ),
        PlayerId.PLAYER_2: Tank(
            PlayerId.PLAYER_2,
            Position(5, 1),
            Direction.DOWN
        )
    }

    bases = {
        PlayerId.PLAYER_1: Base(
            PlayerId.PLAYER_1,
            Position(1, 6)
        ),
        PlayerId.PLAYER_2: Base(
            PlayerId.PLAYER_2,
            Position(5, 0)
        )
    }

    return GameState(
        width=7,
        height=7,
        tanks=tanks,
        bases=bases
    )


def test_default_scenario_creation():
    state = create_default_scenario()

    assert state.width == 13
    assert state.height == 13

    assert len(state.tanks) == 2
    assert len(state.bases) == 2
    assert len(state.walls) == 15

    assert state.current_player == PlayerId.PLAYER_1


def test_position_inside_board():
    state = make_state()

    assert state.is_inside(Position(0, 0))
    assert state.is_inside(Position(6, 6))

    assert not state.is_inside(Position(-1, 0))
    assert not state.is_inside(Position(7, 6))


def test_clone_is_independent():
    original = make_state()

    copied = original.clone()

    copied.tanks[
        PlayerId.PLAYER_1
    ].hp -= 1

    assert original.tanks[
        PlayerId.PLAYER_1
    ].hp == 6

    assert copied.tanks[
        PlayerId.PLAYER_1
    ].hp == 5


def test_clone_does_not_share_walls():
    position = Position(3, 3)

    state = make_state()

    state.walls[position] = Wall(position)

    copied = state.clone()

    copied.walls[position].hp -= 1

    assert state.walls[position].hp == 3
    assert copied.walls[position].hp == 2


def test_initial_state_is_not_terminal():
    state = make_state()

    assert state.is_terminal is False
    assert state.is_draw is False
    assert state.winner is None


def test_destroyed_tank_defeats_player():
    state = make_state()

    state.tanks[PlayerId.PLAYER_1].hp = 0

    assert state.is_terminal is True
    assert state.winner == PlayerId.PLAYER_2


def test_destroyed_base_defeats_player():
    state = make_state()

    state.bases[PlayerId.PLAYER_2].hp = 0

    assert state.is_terminal is True
    assert state.winner == PlayerId.PLAYER_1


def test_both_players_defeated_is_draw():
    state = make_state()

    state.tanks[PlayerId.PLAYER_1].hp = 0
    state.bases[PlayerId.PLAYER_2].hp = 0

    assert state.is_terminal is True
    assert state.is_draw is True
    assert state.winner is None


def test_invalid_board_dimensions():
    with pytest.raises(ValueError):
        GameState(
            width=0,
            height=7,
            tanks={},
            bases={}
        )


def test_invalid_entity_position():
    tanks = {
        PlayerId.PLAYER_1: Tank(
            PlayerId.PLAYER_1,
            Position(10, 10)
        ),
        PlayerId.PLAYER_2: Tank(
            PlayerId.PLAYER_2,
            Position(5, 1)
        )
    }

    bases = {
        PlayerId.PLAYER_1: Base(
            PlayerId.PLAYER_1,
            Position(1, 6)
        ),
        PlayerId.PLAYER_2: Base(
            PlayerId.PLAYER_2,
            Position(5, 0)
        )
    }

    with pytest.raises(ValueError):
        GameState(
            width=7,
            height=7,
            tanks=tanks,
            bases=bases
        )
