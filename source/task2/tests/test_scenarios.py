import pytest

from tank_battle.constants import (
    PlayerId,
    Direction,
    Action,
)

from tank_battle.entities import Position

from tank_battle.game_engine import GameEngine

from experiments.scenarios import (
    SCENARIO_FACTORIES,
    create_all_scenarios,
    create_open_scenario,
    create_obstacle_scenario,
    create_combat_scenario,
)


@pytest.mark.parametrize(
    "scenario_name",
    list(SCENARIO_FACTORIES.keys())
)
def test_scenario_is_valid(scenario_name):
    state = SCENARIO_FACTORIES[scenario_name]()

    state.validate()

    assert state.width == 13
    assert state.height == 13

    assert len(state.tanks) == 2
    assert len(state.bases) == 2

    assert state.current_player == PlayerId.PLAYER_1
    assert state.is_terminal is False


def test_open_scenario_has_no_walls():
    state = create_open_scenario()

    assert len(state.walls) == 0


def test_obstacle_scenario_has_walls():
    state = create_obstacle_scenario()

    assert len(state.walls) > 0

    # The central corridor must remain open.
    for x in range(4, 9):
        assert Position(x, 6) not in state.walls


def test_combat_scenario_has_two_bullets():
    state = create_combat_scenario()

    assert len(state.bullets) == 2

    assert state.bullets[0].owner == PlayerId.PLAYER_1
    assert state.bullets[0].direction == Direction.RIGHT

    assert state.bullets[1].owner == PlayerId.PLAYER_2
    assert state.bullets[1].direction == Direction.LEFT

    assert state.next_bullet_id == 3


def test_combat_bullets_hit_both_tanks():
    state = create_combat_scenario()

    engine = GameEngine()

    first = engine.apply_action(
        state,
        Action.STAY,
    )

    second = engine.apply_action(
        first.state,
        Action.STAY,
    )

    result = second.state

    assert result.tanks[PlayerId.PLAYER_1].hp == 5
    assert result.tanks[PlayerId.PLAYER_2].hp == 5

    assert len(result.bullets) == 0


def test_scenario_factories_create_independent_states():
    first = create_open_scenario()
    second = create_open_scenario()

    first.tanks[PlayerId.PLAYER_1].hp = 3

    assert second.tanks[PlayerId.PLAYER_1].hp == 6


def test_create_all_scenarios_returns_four_scenarios():
    scenarios = create_all_scenarios()

    assert len(scenarios) == 4

    assert set(scenarios.keys()) == {
        "S1_Default",
        "S2_Open",
        "S3_Obstacle",
        "S4_Combat",
    }