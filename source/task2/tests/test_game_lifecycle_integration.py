"""Integration tests for Tank Battle game lifecycle and terminal rules."""

import pytest

from tank_battle.constants import Action, Direction, PlayerId
from tank_battle.entities import Position, Tank, Base
from tank_battle.game_state import GameState
from tank_battle.game_engine import GameEngine, GameRuleError
from tank_battle.agents import RandomAgent, AgentError


def make_state(
    *,
    p1_position=Position(1, 4),
    p2_position=Position(6, 2),
    p1_base=Position(0, 6),
    p2_base=Position(6, 0),
    p1_facing=Direction.RIGHT,
    p2_facing=Direction.DOWN,
    p1_tank_hp=6,
    p2_tank_hp=6,
    p1_base_hp=9,
    p2_base_hp=9,
):
    """Build a small valid board for focused lifecycle tests."""
    tanks = {
        PlayerId.PLAYER_1: Tank(
            PlayerId.PLAYER_1,
            p1_position,
            p1_facing,
            p1_tank_hp,
        ),
        PlayerId.PLAYER_2: Tank(
            PlayerId.PLAYER_2,
            p2_position,
            p2_facing,
            p2_tank_hp,
        ),
    }
    bases = {
        PlayerId.PLAYER_1: Base(
            PlayerId.PLAYER_1,
            p1_base,
            p1_base_hp,
        ),
        PlayerId.PLAYER_2: Base(
            PlayerId.PLAYER_2,
            p2_base,
            p2_base_hp,
        ),
    }
    return GameState(
        width=7,
        height=7,
        tanks=tanks,
        bases=bases,
    )


def finish_current_cycle(state, first_action, second_action):
    """Apply both players' actions and return the second transition."""
    first = GameEngine.apply_action(state, first_action)
    second = GameEngine.apply_action(first.state, second_action)
    return second


def test_player_one_wins_by_destroying_player_two_base():
    state = make_state(
        p2_base=Position(4, 4),
        p2_base_hp=1,
    )

    result = finish_current_cycle(
        state,
        Action.FIRE,
        Action.STAY,
    )

    assert result.state.is_terminal is True
    assert result.state.is_draw is False
    assert result.state.winner == PlayerId.PLAYER_1
    assert result.state.bases[PlayerId.PLAYER_2].hp == 0
    assert result.state.cycle_number == 1
    assert any(event.event_type == "bullet_hit_base" for event in result.events)
    assert any(
        event.event_type == "game_over"
        and event.player == PlayerId.PLAYER_1
        for event in result.events
    )


def test_player_two_can_win_by_destroying_player_one_base():
    state = make_state(
        p1_base=Position(6, 5),
        p2_base=Position(5, 0),
        p1_base_hp=1,
    )

    result = finish_current_cycle(
        state,
        Action.STAY,
        Action.FIRE,
    )

    assert result.state.is_terminal is True
    assert result.state.is_draw is False
    assert result.state.winner == PlayerId.PLAYER_2
    assert result.state.bases[PlayerId.PLAYER_1].hp == 0
    assert result.state.cycle_number == 1
    assert any(
        event.event_type == "game_over"
        and event.player == PlayerId.PLAYER_2
        for event in result.events
    )


def test_destroying_opponent_tank_also_ends_the_game():
    state = make_state(
        p2_position=Position(4, 4),
        p2_tank_hp=1,
    )

    result = finish_current_cycle(
        state,
        Action.FIRE,
        Action.STAY,
    )

    assert result.state.is_terminal is True
    assert result.state.winner == PlayerId.PLAYER_1
    assert result.state.tanks[PlayerId.PLAYER_2].hp == 0
    assert any(event.event_type == "bullet_hit_tank" for event in result.events)
    assert any(event.event_type == "game_over" for event in result.events)


def test_terminal_victory_disables_actions_and_rejects_further_turns():
    state = make_state(
        p2_base=Position(4, 4),
        p2_base_hp=1,
    )
    terminal_state = finish_current_cycle(
        state,
        Action.FIRE,
        Action.STAY,
    ).state

    assert GameEngine.get_legal_actions(terminal_state) == ()
    with pytest.raises(GameRuleError):
        GameEngine.apply_action(terminal_state, Action.STAY)
    with pytest.raises(AgentError):
        RandomAgent(seed=7).get_action(terminal_state)


def test_draw_state_is_terminal_and_has_no_unique_winner():
    """Validate model-level draw semantics, not an engine-generated double KO."""
    state = make_state(
        p1_tank_hp=0,
        p2_base_hp=0,
    )

    assert state.is_terminal is True
    assert state.is_draw is True
    assert state.winner is None
    assert GameEngine.get_legal_actions(state) == ()

    with pytest.raises(GameRuleError):
        GameEngine.apply_action(state, Action.STAY)
    with pytest.raises(AgentError):
        RandomAgent(seed=11).get_action(state)


def test_nonterminal_game_has_no_winner_and_can_continue():
    state = make_state()

    assert state.is_terminal is False
    assert state.is_draw is False
    assert state.winner is None
    assert len(GameEngine.get_legal_actions(state)) == len(Action)

    result = finish_current_cycle(
        state,
        Action.STAY,
        Action.STAY,
    )

    assert result.state.is_terminal is False
    assert result.state.current_player == PlayerId.PLAYER_1
    assert result.state.cycle_number == 1
