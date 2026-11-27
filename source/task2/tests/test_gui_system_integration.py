"""End-to-end integration tests for the Tank Battle GUI and AI system."""

import os

# Run Pygame without opening a real desktop window during automated tests.
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import pytest

from tank_battle.constants import Action, PlayerId
from tank_battle.ui.app import TankBattleApp
from tank_battle.agents import get_search_algorithm_names


@pytest.fixture
def app():
    application = TankBattleApp()
    application.search_depth = 1
    application._build_ai_agents()
    yield application
    pygame.quit()


@pytest.mark.parametrize("algorithm_name", get_search_algorithm_names())
def test_each_builtin_algorithm_completes_human_vs_ai_cycle(app, algorithm_name):
    """Each built-in search agent must act through the GUI and GameEngine."""
    app.mode_index = 1  # Human vs AI
    app.algorithm_index = app.algorithm_names.index(algorithm_name)
    app.search_depth = 1
    app._build_ai_agents()

    starting_cycle = app.state.cycle_number

    # Player 1 is human; Player 2 is controlled by the selected AI.
    app._apply_action(Action.STAY, source="Integration Test")
    assert app.state.current_player == PlayerId.PLAYER_2

    app._run_ai_turn()

    assert app.state.current_player == PlayerId.PLAYER_1
    assert app.state.cycle_number == starting_cycle + 1
    assert algorithm_name in app.last_search_info
    assert not app.state.is_terminal


def test_ai_vs_ai_completes_a_full_cycle_through_game_engine(app):
    """Both GUI-managed AI agents must take turns and complete one cycle."""
    app.mode_index = 2  # AI vs AI
    app.search_depth = 1
    app._build_ai_agents()

    assert set(app.ai_agents) == {
        PlayerId.PLAYER_1,
        PlayerId.PLAYER_2,
    }

    app._run_ai_turn()
    assert app.state.current_player == PlayerId.PLAYER_2
    assert app.state.cycle_number == 0

    app._run_ai_turn()
    assert app.state.current_player == PlayerId.PLAYER_1
    assert app.state.cycle_number == 1
    assert "Algorithm:" in app.last_search_info


def test_algorithm_button_rebuilds_agent_and_new_algorithm_runs(app):
    """Changing the algorithm in the GUI must affect the next AI action."""
    app.mode_index = 1  # Human vs AI
    app.search_depth = 1
    previous_algorithm = app.current_algorithm

    app._handle_button("algorithm")
    selected_algorithm = app.current_algorithm

    assert selected_algorithm != previous_algorithm
    assert app.ai_agents[PlayerId.PLAYER_2].name == selected_algorithm

    app._apply_action(Action.STAY, source="Integration Test")
    app._run_ai_turn()

    assert selected_algorithm in app.last_search_info
    assert app.state.current_player == PlayerId.PLAYER_1
    assert app.state.cycle_number == 1


def test_reset_after_ai_cycle_restores_state_and_keeps_ai_configuration(app):
    """Reset must restore the board without losing the current AI mode."""
    app.mode_index = 2  # AI vs AI
    app.search_depth = 1
    app._build_ai_agents()

    app._run_ai_turn()
    app._run_ai_turn()
    assert app.state.cycle_number == 1

    selected_algorithm = app.current_algorithm
    app._handle_button("reset")

    assert app.current_mode == "AI vs AI"
    assert app.state.current_player == PlayerId.PLAYER_1
    assert app.state.cycle_number == 0
    assert set(app.ai_agents) == {
        PlayerId.PLAYER_1,
        PlayerId.PLAYER_2,
    }
    assert all(agent.name == selected_algorithm for agent in app.ai_agents.values())
    assert app.last_search_info == "No AI search performed yet."


def test_terminal_game_is_not_advanced_by_ai_and_can_be_rendered(app):
    """A terminal state must remain unchanged when the AI loop is invoked."""
    app.mode_index = 2  # AI vs AI
    app.search_depth = 1
    app._build_ai_agents()

    app.state.bases[PlayerId.PLAYER_1].hp = 0
    before = app.state.clone()

    app._run_ai_turn()
    app._draw_interface()

    assert app.state.is_terminal
    assert app.state.winner == PlayerId.PLAYER_2
    assert app.state.cycle_number == before.cycle_number
    assert app.state.current_player == before.current_player
    assert app.state.bases[PlayerId.PLAYER_1].hp == 0
