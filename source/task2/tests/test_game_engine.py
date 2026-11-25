
import pytest

from tank_battle.constants import (
    PlayerId,
    Direction,
    Action,
)

from tank_battle.entities import (
    Position,
    Tank,
    Base,
    Wall,
)

from tank_battle.game_state import GameState
from tank_battle.game_engine import (
    GameEngine,
    GameRuleError,
)


def make_state(
    p1_position=Position(1, 4),
    p2_position=Position(6, 2),
    p1_base=Position(0, 6),
    p2_base=Position(6, 0),
    p1_facing=Direction.RIGHT,
    walls=None
):
    tanks = {
        PlayerId.PLAYER_1: Tank(
            PlayerId.PLAYER_1,
            p1_position,
            p1_facing
        ),

        PlayerId.PLAYER_2: Tank(
            PlayerId.PLAYER_2,
            p2_position,
            Direction.DOWN
        )
    }

    bases = {
        PlayerId.PLAYER_1: Base(
            PlayerId.PLAYER_1,
            p1_base
        ),

        PlayerId.PLAYER_2: Base(
            PlayerId.PLAYER_2,
            p2_base
        )
    }

    wall_dict = {
        position: Wall(position)
        for position in (walls or [])
    }

    return GameState(
        width=7,
        height=7,
        tanks=tanks,
        bases=bases,
        walls=wall_dict
    )


def test_all_six_actions_are_available():
    state = make_state()

    actions = GameEngine.get_legal_actions(state)

    assert len(actions) == 6
    assert set(actions) == set(Action)


def test_first_player_action_changes_turn():
    state = make_state()

    result = GameEngine.apply_action(
        state,
        Action.STAY
    )

    assert (
        result.state.current_player
        == PlayerId.PLAYER_2
    )

    assert result.state.cycle_number == 0


def test_second_player_action_completes_cycle():
    state = make_state()

    first = GameEngine.apply_action(
        state,
        Action.STAY
    )

    second = GameEngine.apply_action(
        first.state,
        Action.STAY
    )

    assert (
        second.state.current_player
        == PlayerId.PLAYER_1
    )

    assert second.state.cycle_number == 1

    assert any(
        event.event_type == "cycle_completed"
        for event in second.events
    )


def test_tank_moves_exactly_one_cell():
    state = make_state()

    result = GameEngine.apply_action(
        state,
        Action.MOVE_UP
    )

    tank = result.state.tanks[
        PlayerId.PLAYER_1
    ]

    assert tank.position == Position(1, 3)
    assert tank.facing == Direction.UP


def test_tank_cannot_leave_board():
    state = make_state(
        p1_position=Position(2, 0),
        p1_facing=Direction.UP
    )

    result = GameEngine.apply_action(
        state,
        Action.MOVE_UP
    )

    tank = result.state.tanks[
        PlayerId.PLAYER_1
    ]

    assert tank.position == Position(2, 0)
    assert tank.facing == Direction.UP

    assert any(
        event.event_type == "movement_blocked"
        for event in result.events
    )


def test_tank_cannot_move_through_wall():
    state = make_state(
        p1_position=Position(2, 4),
        p1_facing=Direction.RIGHT,
        walls=[Position(3, 4)]
    )

    result = GameEngine.apply_action(
        state,
        Action.MOVE_RIGHT
    )

    tank = result.state.tanks[
        PlayerId.PLAYER_1
    ]

    assert tank.position == Position(2, 4)
    assert Position(3, 4) in result.state.walls


def test_tank_cannot_move_into_opponent_tank():
    state = make_state(
        p1_position=Position(2, 4),
        p2_position=Position(2, 3)
    )

    result = GameEngine.apply_action(
        state,
        Action.MOVE_UP
    )

    assert (
        result.state.tanks[PlayerId.PLAYER_1].position
        == Position(2, 4)
    )


def test_tank_cannot_move_into_base():
    state = make_state(
        p1_position=Position(2, 4),
        p1_base=Position(2, 3)
    )

    result = GameEngine.apply_action(
        state,
        Action.MOVE_UP
    )

    assert (
        result.state.tanks[PlayerId.PLAYER_1].position
        == Position(2, 4)
    )


def test_stay_does_not_change_position():
    state = make_state()

    result = GameEngine.apply_action(
        state,
        Action.STAY
    )

    assert (
        result.state.tanks[PlayerId.PLAYER_1].position
        == Position(1, 4)
    )


def test_fire_creates_bullet():
    state = make_state()

    result = GameEngine.apply_action(
        state,
        Action.FIRE
    )

    assert len(result.state.bullets) == 1

    bullet = result.state.bullets[0]

    assert bullet.owner == PlayerId.PLAYER_1
    assert bullet.position == Position(1, 4)
    assert bullet.direction == Direction.RIGHT
    assert bullet.bullet_id == 1


def test_bullet_moves_three_cells_per_cycle():
    state = make_state()

    first = GameEngine.apply_action(
        state,
        Action.FIRE
    )

    second = GameEngine.apply_action(
        first.state,
        Action.STAY
    )

    assert len(second.state.bullets) == 1

    bullet = second.state.bullets[0]

    assert bullet.position == Position(4, 4)
    assert second.state.cycle_number == 1


def test_bullet_stops_at_first_wall():
    state = make_state(
        walls=[Position(3, 4)]
    )

    first = GameEngine.apply_action(
        state,
        Action.FIRE
    )

    second = GameEngine.apply_action(
        first.state,
        Action.STAY
    )

    assert Position(3, 4) in second.state.walls

    assert (
        second.state.walls[Position(3, 4)].hp == 2
    )

    assert len(second.state.bullets) == 0

    assert any(
        event.event_type == "bullet_hit_wall"
        for event in second.events
    )


def test_wall_is_destroyed_after_three_hits():
    wall_position = Position(3, 4)

    state = make_state(
        walls=[wall_position]
    )

    engine = GameEngine

    for _ in range(3):

        first = engine.apply_action(
            state,
            Action.FIRE
        )

        second = engine.apply_action(
            first.state,
            Action.STAY
        )

        state = second.state

    assert wall_position not in state.walls


def test_bullet_damages_tank():
    state = make_state(
        p2_position=Position(3, 4)
    )

    first = GameEngine.apply_action(
        state,
        Action.FIRE
    )

    second = GameEngine.apply_action(
        first.state,
        Action.STAY
    )

    target = second.state.tanks[
        PlayerId.PLAYER_2
    ]

    assert target.hp == 5


def test_bullet_damages_base():
    state = make_state(
        p2_base=Position(3, 4)
    )

    # Set the target base to 2 HP.
    state.bases[
        PlayerId.PLAYER_2
    ].hp = 2

    first = GameEngine.apply_action(
        state,
        Action.FIRE
    )

    second = GameEngine.apply_action(
        first.state,
        Action.STAY
    )

    target = second.state.bases[
        PlayerId.PLAYER_2
    ]

    assert target.hp == 1
    assert second.state.is_terminal is False


def test_destroying_base_ends_game():
    state = make_state(
        p2_base=Position(3, 4)
    )

    state.bases[
        PlayerId.PLAYER_2
    ].hp = 1

    first = GameEngine.apply_action(
        state,
        Action.FIRE
    )

    second = GameEngine.apply_action(
        first.state,
        Action.STAY
    )

    assert second.state.is_terminal is True

    assert (
        second.state.winner
        == PlayerId.PLAYER_1
    )

    assert len(second.state.bullets) == 0

    assert any(
        event.event_type == "game_over"
        for event in second.events
    )


def test_bullet_disappears_outside_board():
    state = make_state(
        p1_position=Position(2, 0),
        p1_facing=Direction.UP
    )

    first = GameEngine.apply_action(
        state,
        Action.FIRE
    )

    second = GameEngine.apply_action(
        first.state,
        Action.STAY
    )

    assert len(second.state.bullets) == 0

    assert any(
        event.event_type == "bullet_out_of_bounds"
        for event in second.events
    )


def test_original_state_is_not_modified():
    state = make_state()

    original_position = state.tanks[
        PlayerId.PLAYER_1
    ].position

    result = GameEngine.apply_action(
        state,
        Action.MOVE_UP
    )

    assert state.tanks[
        PlayerId.PLAYER_1
    ].position == original_position

    assert result.state.tanks[
        PlayerId.PLAYER_1
    ].position != original_position


def test_invalid_action():
    state = make_state()

    with pytest.raises(GameRuleError):
        GameEngine.apply_action(
            state,
            "INVALID_ACTION"
        )


def test_cannot_play_after_game_over():
    state = make_state()

    state.bases[
        PlayerId.PLAYER_2
    ].hp = 0

    with pytest.raises(GameRuleError):
        GameEngine.apply_action(
            state,
            Action.STAY
        )
