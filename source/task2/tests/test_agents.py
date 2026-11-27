import pytest

from tank_battle.constants import Action
from tank_battle.scenario import create_default_scenario

from tank_battle.agents import (
    RandomAgent,
    create_search_agent,
    get_search_algorithm_names,
    AgentError,
)


def test_random_agent_returns_valid_action():
    state = create_default_scenario()
    agent = RandomAgent(seed=42)

    action = agent.get_action(state)

    assert isinstance(action, Action)


def test_random_agent_is_reproducible_with_same_seed():
    state = create_default_scenario()

    first_agent = RandomAgent(seed=42)
    second_agent = RandomAgent(seed=42)

    first_action = first_agent.get_action(state)
    second_action = second_agent.get_action(state)

    assert first_action == second_action


@pytest.mark.parametrize(
    "algorithm",
    get_search_algorithm_names(),
)
def test_search_adapter_returns_valid_action(algorithm):
    state = create_default_scenario()
    agent = create_search_agent(
        algorithm=algorithm,
        depth=1,
    )

    action = agent.get_action(state)

    assert isinstance(action, Action)
    assert agent.last_result is not None
    assert agent.last_result.best_action == action


@pytest.mark.parametrize(
    "algorithm",
    get_search_algorithm_names(),
)
def test_search_adapter_preserves_original_state(algorithm):
    state = create_default_scenario()

    original_player = state.current_player
    original_positions = {
        player: tank.position
        for player, tank in state.tanks.items()
    }

    agent = create_search_agent(
        algorithm=algorithm,
        depth=1,
    )

    agent.get_action(state)

    assert state.current_player == original_player

    assert {
        player: tank.position
        for player, tank in state.tanks.items()
    } == original_positions


def test_agent_rejects_terminal_state():
    state = create_default_scenario()
    state.tanks[state.current_player].hp = 0

    agent = RandomAgent(seed=42)

    with pytest.raises(AgentError):
        agent.get_action(state)


def test_search_adapter_rejects_unknown_algorithm():
    with pytest.raises(ValueError):
        create_search_agent(
            algorithm="Unknown Algorithm",
            depth=1,
        )