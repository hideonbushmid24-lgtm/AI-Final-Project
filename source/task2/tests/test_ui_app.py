import os

# Use a virtual display so UI tests can run without opening a window.
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import pytest

from tank_battle.constants import (
    Action,
    PlayerId,
)

from tank_battle.ui.app import TankBattleApp


@pytest.fixture
def app():
    application = TankBattleApp()
    application.search_depth = 1

    yield application

    pygame.quit()


def test_app_starts_in_human_vs_ai_mode(app):
    assert app.current_mode == "Human vs AI"

    assert PlayerId.PLAYER_1 not in app.ai_agents
    assert PlayerId.PLAYER_2 in app.ai_agents


def test_player_one_keyboard_moves_tank(app):
    tank = app.state.tanks[PlayerId.PLAYER_1]
    original_position = tank.position

    app._handle_keydown(pygame.K_w)

    assert (
        app.state.tanks[PlayerId.PLAYER_1].position
        != original_position
    )

    assert app.state.current_player == PlayerId.PLAYER_2


def test_human_cannot_control_ai_turn(app):
    # Player 1 moves, making it Player 2's AI turn.
    app._handle_keydown(pygame.K_w)

    original_position = (
        app.state.tanks[PlayerId.PLAYER_2].position
    )

    app._handle_keydown(pygame.K_UP)

    assert (
        app.state.tanks[PlayerId.PLAYER_2].position
        == original_position
    )


def test_ai_vs_ai_creates_two_agents(app):
    app._change_mode()

    assert app.current_mode == "AI vs AI"

    assert PlayerId.PLAYER_1 in app.ai_agents
    assert PlayerId.PLAYER_2 in app.ai_agents


def test_ai_vs_ai_can_execute_one_turn(app):
    app._change_mode()
    app.search_depth = 1
    app._build_ai_agents()

    original_player = app.state.current_player

    app._run_ai_turn()

    assert app.state.current_player != original_player
    assert "Algorithm:" in app.last_search_info


def test_reset_restores_default_scenario(app):
    original_position = (
        app.state.tanks[PlayerId.PLAYER_1].position
    )

    app._apply_action(Action.MOVE_UP)

    app._reset_game()

    assert (
        app.state.tanks[PlayerId.PLAYER_1].position
        == original_position
    )

    assert app.state.current_player == PlayerId.PLAYER_1
    assert app.state.cycle_number == 0


def test_depth_is_limited_to_three(app):
    app.search_depth = 3
    app._change_depth(1)

    assert app.search_depth == 3

    app.search_depth = 1
    app._change_depth(-1)

    assert app.search_depth == 1