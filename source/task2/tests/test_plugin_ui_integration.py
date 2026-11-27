"""Integration tests for external plugins running through the Pygame GUI."""

import os

# Keep GUI tests headless, matching the existing test_ui_app.py setup.
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import pytest

from tank_battle.constants import Action, PlayerId
from tank_battle.ui.app import TankBattleApp


PLUGIN_STAY = '''
from tank_battle.agents.base_agent import BaseAgent
from tank_battle.constants import Action

class UIIntegrationStayAgent(BaseAgent):
    name = "UI Integration Stay Agent"

    def select_action(self, state):
        return Action.STAY
'''


PLUGIN_INVALID = '''
from tank_battle.agents.base_agent import BaseAgent

class UIIntegrationInvalidAgent(BaseAgent):
    name = "UI Integration Invalid Agent"

    def select_action(self, state):
        return "TELEPORT"
'''


@pytest.fixture
def app():
    application = TankBattleApp()
    application.search_depth = 1
    yield application
    pygame.quit()


def _write_plugin(tmp_path, filename, source):
    plugin_file = tmp_path / filename
    plugin_file.write_text(source, encoding="utf-8")
    return str(plugin_file.resolve())


def _configure_plugin(app, plugin_path, class_name="UIIntegrationStayAgent"):
    app.plugin_path = plugin_path
    app.plugin_class_name = class_name
    app.use_plugin = True
    app._build_ai_agents()


def test_external_plugin_controls_player_two_in_human_vs_ai(app, tmp_path):
    plugin_path = _write_plugin(
        tmp_path,
        "ui_stay_agent.py",
        PLUGIN_STAY,
    )
    _configure_plugin(app, plugin_path)

    assert PlayerId.PLAYER_1 not in app.ai_agents
    assert PlayerId.PLAYER_2 in app.ai_agents

    # The human completes Player 1's turn; the external plugin controls P2.
    app._apply_action(Action.STAY, source="Human")
    assert app.state.current_player == PlayerId.PLAYER_2

    app._run_ai_turn()

    assert app.state.current_player == PlayerId.PLAYER_1
    assert app.state.cycle_number == 1
    assert app.last_search_info == "Agent: UI Integration Stay Agent"
    assert "AI error" not in app.last_message


def test_ai_vs_ai_uses_separate_plugin_instances(app, tmp_path):
    plugin_path = _write_plugin(
        tmp_path,
        "ui_two_player_agent.py",
        PLUGIN_STAY,
    )
    app.plugin_path = plugin_path
    app.plugin_class_name = "UIIntegrationStayAgent"
    app.use_plugin = True

    # Default mode is Human vs AI; next mode is AI vs AI.
    app._change_mode()

    player_one_agent = app.ai_agents[PlayerId.PLAYER_1]
    player_two_agent = app.ai_agents[PlayerId.PLAYER_2]

    assert player_one_agent is not player_two_agent

    app._run_ai_turn()
    assert app.state.current_player == PlayerId.PLAYER_2
    assert app.state.cycle_number == 0

    app._run_ai_turn()
    assert app.state.current_player == PlayerId.PLAYER_1
    assert app.state.cycle_number == 1
    assert not app.state.is_terminal


def test_invalid_plugin_action_pauses_gui_without_changing_game_state(app, tmp_path):
    plugin_path = _write_plugin(
        tmp_path,
        "ui_invalid_agent.py",
        PLUGIN_INVALID,
    )
    _configure_plugin(
        app,
        plugin_path,
        class_name="UIIntegrationInvalidAgent",
    )

    # Advance to the AI player's turn.
    app._apply_action(Action.STAY, source="Human")
    assert app.state.current_player == PlayerId.PLAYER_2
    state_before_ai_action = app.state.clone()

    app._run_ai_turn()

    assert app.state == state_before_ai_action
    assert app.state.current_player == PlayerId.PLAYER_2
    assert app.paused is True
    assert "AI error" in app.last_message


def test_clearing_plugin_restores_builtin_search_agent(app, tmp_path):
    plugin_path = _write_plugin(
        tmp_path,
        "ui_clearable_agent.py",
        PLUGIN_STAY,
    )
    _configure_plugin(app, plugin_path)
    assert app.use_plugin is True

    app._clear_plugin()

    assert app.use_plugin is False
    assert app.plugin_path is None
    assert app.plugin_class_name is None
    assert PlayerId.PLAYER_2 in app.ai_agents
    assert type(app.ai_agents[PlayerId.PLAYER_2]).__name__ == "SearchAgentAdapter"
    assert app.ai_agents[PlayerId.PLAYER_2].last_result is None
