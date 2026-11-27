"""End-to-end integration tests for Tank Battle gameplay and agents."""

import pytest

from tank_battle.constants import Action, Direction, PlayerId
from tank_battle.entities import Base, Position, Tank
from tank_battle.game_engine import GameEngine, GameRuleError
from tank_battle.game_state import GameState
from tank_battle.scenario import create_default_scenario
from tank_battle.agents import (
    AgentError,
    PluginLoader,
    RandomAgent,
    create_search_agent,
    get_search_algorithm_names,
)


PLUGIN_STAY = '''
from tank_battle.agents.base_agent import BaseAgent
from tank_battle.constants import Action

class IntegrationStayAgent(BaseAgent):
    name = "Integration Stay Agent"

    def select_action(self, state):
        return Action.STAY
'''


PLUGIN_FIRE = '''
from tank_battle.agents.base_agent import BaseAgent
from tank_battle.constants import Action

class IntegrationFireAgent(BaseAgent):
    name = "Integration Fire Agent"

    def select_action(self, state):
        return Action.FIRE
'''


PLUGIN_INVALID = '''
from tank_battle.agents.base_agent import BaseAgent

class IntegrationInvalidAgent(BaseAgent):
    name = "Integration Invalid Agent"

    def select_action(self, state):
        return "TELEPORT"
'''


def _write_plugin(tmp_path, filename, content):
    plugin_file = tmp_path / filename
    plugin_file.write_text(content, encoding="utf-8")
    return plugin_file


def _make_finishing_scenario():
    """Place Player 2's one-HP base exactly three cells ahead of P1."""
    tanks = {
        PlayerId.PLAYER_1: Tank(
            PlayerId.PLAYER_1,
            Position(1, 1),
            Direction.RIGHT,
        ),
        PlayerId.PLAYER_2: Tank(
            PlayerId.PLAYER_2,
            Position(10, 10),
            Direction.LEFT,
        ),
    }
    bases = {
        PlayerId.PLAYER_1: Base(
            PlayerId.PLAYER_1,
            Position(1, 2),
        ),
        PlayerId.PLAYER_2: Base(
            PlayerId.PLAYER_2,
            Position(4, 1),
            hp=1,
        ),
    }
    return GameState(
        width=13,
        height=13,
        tanks=tanks,
        bases=bases,
        current_player=PlayerId.PLAYER_1,
    )


@pytest.mark.parametrize("algorithm", get_search_algorithm_names())
def test_search_agent_and_random_agent_complete_a_game_cycle(algorithm):
    """Each search implementation must produce an engine-executable move."""
    state = create_default_scenario()
    search_agent = create_search_agent(algorithm=algorithm, depth=1)
    agents = {
        PlayerId.PLAYER_1: search_agent,
        PlayerId.PLAYER_2: RandomAgent(seed=2026),
    }
    engine = GameEngine()

    for player in (PlayerId.PLAYER_1, PlayerId.PLAYER_2):
        assert state.current_player == player
        state_before_action = state.clone()

        action = agents[player].get_action(state)
        assert action in engine.get_legal_actions(state)

        transition = engine.apply_action(state, action)

        # Neither agent selection nor the engine may mutate the input state.
        assert state == state_before_action

        state = transition.state
        state.validate()
        assert state.current_player == player.opponent

    assert state.current_player == PlayerId.PLAYER_1
    assert state.cycle_number == 1
    assert not state.is_terminal


def test_external_plugin_agent_action_is_executed_by_game_engine(tmp_path):
    plugin_file = _write_plugin(
        tmp_path,
        "integration_stay_agent.py",
        PLUGIN_STAY,
    )
    agent = PluginLoader.load_agent(
        plugin_file,
        "IntegrationStayAgent",
    )
    state = create_default_scenario()

    action = agent.get_action(state)
    transition = GameEngine.apply_action(state, action)

    assert action == Action.STAY
    assert transition.state.current_player == PlayerId.PLAYER_2
    assert transition.state.cycle_number == 0
    assert any(event.event_type == "tank_stayed" for event in transition.events)
    assert state.current_player == PlayerId.PLAYER_1


def test_plugin_and_engine_complete_a_winning_bullet_sequence(tmp_path):
    plugin_file = _write_plugin(
        tmp_path,
        "integration_fire_agent.py",
        PLUGIN_FIRE,
    )
    agent = PluginLoader.load_agent(
        plugin_file,
        "IntegrationFireAgent",
    )
    state = _make_finishing_scenario()

    # P1's plugin fires. The engine creates a bullet and passes the turn to P2.
    first_transition = GameEngine.apply_action(
        state,
        agent.get_action(state),
    )
    assert first_transition.state.current_player == PlayerId.PLAYER_2
    assert len(first_transition.state.bullets) == 1

    # P2's action completes the cycle; the bullet reaches P2's base.
    final_transition = GameEngine.apply_action(
        first_transition.state,
        Action.STAY,
    )
    final_state = final_transition.state
    final_state.validate()

    assert final_state.bases[PlayerId.PLAYER_2].hp == 0
    assert final_state.is_terminal
    assert not final_state.is_draw
    assert final_state.winner == PlayerId.PLAYER_1
    assert final_state.bullets == []
    assert GameEngine.get_legal_actions(final_state) == ()
    assert any(event.event_type == "game_over" for event in final_transition.events)

    with pytest.raises(GameRuleError):
        GameEngine.apply_action(final_state, Action.STAY)


def test_invalid_plugin_action_is_rejected_before_reaching_game_engine(tmp_path):
    plugin_file = _write_plugin(
        tmp_path,
        "integration_invalid_agent.py",
        PLUGIN_INVALID,
    )
    agent = PluginLoader.load_agent(
        plugin_file,
        "IntegrationInvalidAgent",
    )
    state = create_default_scenario()

    with pytest.raises(AgentError, match="invalid action"):
        agent.get_action(state)

    # The game remains unchanged because no action was passed to the engine.
    assert state.current_player == PlayerId.PLAYER_1
    assert state.cycle_number == 0
